# coding:utf-8
import logging
import hashlib
import config
import re
import json
import CONTENT

from libs.response_code import RET
from libs.login_verify import require_logined
from .BaseHandler import *
from libs import qiniu_image_storage

class HouseindexHandler(BaseHandler):
    """提供城区信息"""
    def get(self):
        # 该方法通过自动获取客户端ip调取该客户城区信息
        # try:
        #     from IP import  find
        # except Exception as e:
        #     logging.error(e)
        #
        # # 获取客户端IP
        # remote_ip = self.request.remote_ip
        # # 通过IP模块获取城市
        # city = find(remote_ip).split("\t")[2]
        # # 从数据库中调取城市区域信息
        # sql1 = "select ai_area_id from ih_area_info where ai_name = %(city)s;"
        #
        # sql2= "select ai_area_id,ai_name from ih_area_info where ai_parea_id = %(id)s;"
        # try:
        #     ret1 = self.db.query(sql1,city = city)
        #     ret2 = self.db.query(sql2,id = ret1['ai_area_id'])
        # except Exception as e:
        #     logging.error(e)
        #     return self.write(dict(errcode=RET.DBERR, errmsg="数据库查询出错"))
        # if not ret2:
        #     return self.write(dict(errcode=RET.NODATA, errmsg="没有数据"))
        # # 保存转换好的区域信息
        # data = []
        # for row in ret2:
        #     d = {
        #         "area_id": row.get("ai_area_id", ""),
        #         "name": row.get("ai_name", "")
        #     }
        #     data.append(d)
        #
        # return self.write(dict(errcode=RET.OK, errmsg="OK", data=data))

        # 该方法用于测试，先到redis中查询数据，如果获取到了数据，直接返回给用户

        try:
            ret = self.redis.get("area_info")
        except Exception as e:
            logging.error(e)
            ret = None

        if ret:
            # 此时从redis中读取到的数据ret是json格式字符串
            # ret = "[]"
            # 需要回传的响应数据格式json，形如：
            # '{"errcode":"0", "errmsg":"OK", "data":[]}'
            # '{"errcode":"0", "errmsg":"OK", "data":%s}' % ret
            logging.info("hit redis: area_info")
            info = json.loads(ret.decode('utf-8'))
            # resp = '{"errno":"0", "errmsg":"OK", "data":%s}' % ret.decode('utf-8')

            return self.write(dict(errno=RET.OK, errmsg="OK", data=info))


        # 查询Mysql数据库，获取城区信息
        sql = "select ai_area_id,ai_name from ih_area_info;"
        try:
            ret = self.db.query(sql)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="数据库查询出错"))
        if not ret:
            return self.write(dict(errno=RET.NODATA, errmsg="没有数据"))
        # 保存转换好的区域信息
        data = []
        for row in ret:
            d = {
                "area_id": row.get("ai_area_id", ""),
                "name": row.get("ai_name", "")
            }
            data.append(d)

        # 在返回给用户数据之前，先向redis中保存一份数据的副本

        json_data = json.dumps(data)

        try:
            self.redis.setex("area_info", CONTENT.REDIS_AREA_INFO_EXPIRES_SECONDES,
                             json_data)
        except Exception as e:
            logging.error(e)

        self.write(dict(errno=RET.OK, errmsg="OK", data=data))

class HouseareaHandler(BaseHandler):
    @require_logined
    def get(self):
        try:
            ret = self.redis.get("area_info")
        except Exception as e:
            logging.error(e)
            ret = None

        if ret:
            logging.info("hit redis: area_info")
            info = json.loads(ret.decode('utf-8'))
            return self.write(dict(errno=RET.OK, errmsg="OK", data=info))
        else:
            return self.write(dict(errno=RET.SESSIONERR, errmsg="NO"))

class MyhouseHandler(BaseHandler):
    @require_logined
    def get(self):

        user_id = self.get_current_user()['user']


class HouseinfoHandler(BaseHandler):
    @require_logined
    def post(self):
        user_id = self.get_current_user()['user']
        title = self.json_args.get("title")
        price = self.json_args.get("price")
        area_id = self.json_args.get("area_id")
        address = self.json_args.get("address")
        room_count = self.json_args.get("room_count")
        acreage = self.json_args.get("acreage")
        unit = self.json_args.get("unit")
        capacity = self.json_args.get("capacity")
        beds = self.json_args.get("beds")
        deposit = self.json_args.get("deposit")
        min_days = self.json_args.get("min_days")
        max_days = self.json_args.get("max_days")
        facility = self.json_args.get("facility")  # 对一个房屋的设施，是列表类型
        # 校验

        if not all((title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days,
                    max_days)):

            return self.write(dict(errno=RET.PARAMERR, errmsg="缺少参数"))

        try:
            price = int(price) * 100
            deposit = int(deposit) * 100
        except Exception as e:
            return self.write(dict(errno=RET.PARAMERR, errmsg="参数错误"))

        # 数据
        try:
            sql = "insert into ih_house_info(hi_user_id,hi_title,hi_price,hi_area_id,hi_address,hi_room_count," \
                  "hi_acreage,hi_house_unit,hi_capacity,hi_beds,hi_deposit,hi_min_days,hi_max_days)" \
                  "values(%(user_id)s,%(title)s,%(price)s,%(area_id)s,%(address)s,%(room_count)s,%(acreage)s," \
                  "%(house_unit)s,%(capacity)s,%(beds)s,%(deposit)s,%(min_days)s,%(max_days)s)"
            # 对于insert语句，execute方法会返回最后一个自增id
            house_id = self.db.execute(sql, user_id=user_id, title=title, price=price, area_id=area_id,
                                       address=address,room_count=room_count, acreage=acreage, house_unit=unit,
                                       capacity=capacity,beds=beds, deposit=deposit, min_days=min_days, max_days=max_days)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="save data error"))

        # 将设施列表转换成json字符串保存到数据库中
        facility_id_str = json.dumps(facility)

        try:
            sql = "insert into ih_house_facility(hf_house_id,hf_facility_id_list) values (%(house_id)s,%(facility_id)s)"

            hf_id = self.db.execute(sql,house_id=house_id,facility_id =facility_id_str)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="save data error"))






        return self.write(dict(errno=RET.OK, errmsg="saved data",house_id=house_id))


class HouseimageHandler(BaseHandler):

    @require_logined
    def post(self):
        user_id = self.get_current_user()['user']
        # 获取用户房间上传图片数据
        house_id = self.get_argument("house_id")
        try:
            house_data = self.request.files['house_image'][0]['body']
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DATAERR, errmsg="房屋图片上传失败"))

        # 将数据上传到云空间，取得文件名key
        try:
            # 将头像数据上传到七牛云
            key = qiniu_image_storage.storage(house_data)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DATAERR, errmsg="头像上传云端失败"))

        # 将头像key存入数据库
        try:
            update_avatar = self.db.execute("insert into ih_house_image(hi_house_id,hi_url) values(%(house_id)s, %(key)s);",house_id=house_id, key=key)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="房屋图片更新失败"))
        return self.write(dict(errno=RET.OK, errmsg="房屋图片保存成功", data=CONTENT.QINIU_IMAGE_LINK + '/' + key))