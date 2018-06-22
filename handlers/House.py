# coding:utf-8
import logging
import math
import hashlib
import config
import re
import json
import CONTENT

from libs.response_code import RET
from libs.login_verify import require_logined
from .BaseHandler import *
from libs import qiniu_image_storage

class HouseIndexHandler(BaseHandler):
    """主页信息查询，页面滑动房屋信息，城区信息"""
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
            area_info = self.redis.get("area_info")
            houses_info = self.redis.get("houses_info")
        except Exception as e:
            logging.error(e)
            area_info = None

        if area_info and houses_info:
            # 此时从redis中读取到的数据ret是json格式字符串
            # ret = "[]"
            # 需要回传的响应数据格式json，形如：
            # '{"errcode":"0", "errmsg":"OK", "data":[]}'
            # '{"errcode":"0", "errmsg":"OK", "data":%s}' % ret
            logging.info("hit redis: area_info")
            a_info = json.loads(area_info.decode('utf-8'))
            h_info = json.loads(houses_info.decode('utf-8'))

            # resp = '{"errno":"0", "errmsg":"OK", "data":%s}' % ret.decode('utf-8')

            return self.write(dict(errno=RET.OK, errmsg="OK", data=a_info,houses=h_info))


        # 查询Mysql数据库，获取城区信息
        sql = "select ai_area_id,ai_name from ih_area_info;"
        try:
            area_info = self.db.query(sql)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="数据库查询出错"))
        if not area_info:
            return self.write(dict(errno=RET.NODATA, errmsg="没有数据"))
        # 保存转换好的区域信息
        data = []
        for row in area_info:
            d = {
                "area_id": row.get("ai_area_id", ""),
                "name": row.get("ai_name", "")
            }
            data.append(d)

        # 查询主页滑动展示房屋的信息
        sql = "select hi_house_id,hi_title,hi_index_image_url from ih_house_info order by hi_order_count desc limit 4;"
        try:
            houses_info = self.db.query(sql)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="数据库查询出错"))
        if not houses_info:
            return self.write(dict(errno=RET.NODATA, errmsg="没有数据"))

        houses = []
        for row in houses_info:
            a = {
                "house_id": row.get("hi_house_id", ""),
                "img_url": CONTENT.QINIU_IMAGE_LINK + '/'+ row.get("hi_index_image_url", ""),
                "title": row.get("hi_title", ""),
            }
            houses.append(a)

        # 在返回给用户数据之前，先向redis中保存一份地区数据的副本

        json_data = json.dumps(data)
        houses_data = json.dumps(houses)

        try:
            self.redis.setex("area_info", CONTENT.REDIS_AREA_INFO_EXPIRES_SECONDES,
                             json_data)
        except Exception as e:
            logging.error(e)

        # 在返回给用户数据之前，先向redis中保存一份房屋数据的副本
        try:
            self.redis.setex("houses_info", CONTENT.REDIS_IMAGE_INFO_EXPIRES_SECONDES,
                             houses_data)
        except Exception as e:
            logging.error(e)

        self.write(dict(errno=RET.OK, errmsg="OK", data=data, houses=houses))

class HouseAreaHandler(BaseHandler):
    """创建新房源地区信息调取"""
    @require_logined
    def get(self):
        try:
            area_info = self.redis.get("area_info")
        except Exception as e:
            logging.error(e)
            area_info = None

        if area_info:
            logging.info("hit redis: area_info")
            info = json.loads(area_info.decode('utf-8'))
            return self.write(dict(errno=RET.OK, errmsg="OK", data=info))
        else:
            return self.write(dict(errno=RET.SESSIONERR, errmsg="NO"))

class MyHouseHandler(BaseHandler):
    """获取我的房源页面获取本人上传的房屋信息"""
    @require_logined
    def get(self):

        user_id = self.get_current_user()['user']
        try:
            sql = "select a.hi_house_id,a.hi_title,a.hi_price,a.hi_ctime,b.ai_name,a.hi_index_image_url " \
                  "from ih_house_info a inner join ih_area_info b on a.hi_area_id=b.ai_area_id where a.hi_user_id=%s;"
            house_info = self.db.query(sql,user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errno": RET.DBERR, "errmsg": "get data erro"})
        houses = []
        for i in house_info:
            house = {
                "house_id": i["hi_house_id"],
                "title": i["hi_title"],
                "price": i["hi_price"],
                "ctime": i["hi_ctime"].strftime("%Y-%m-%d"),  # 将返回的Datatime类型格式化为字符串
                "area_name": i["ai_name"],
                "img_url": CONTENT.QINIU_IMAGE_LINK + '/' +i["hi_index_image_url"] if i["hi_index_image_url"] else ""
            }
            houses.append(house)
        return self.write({"errno":RET.OK, "errmsg":"OK", "houses":houses})



class HouseInfoHandler(BaseHandler):
    """房屋信息详情"""
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

    def get(self):
        """获取房屋信息"""
        user_id = self.get_current_user()['user']
        house_id = self.get_argument("house_id")
        # 校验参数
        if not house_id:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))
        # 获取房屋信息

        try:
            sql = "select hi_title,hi_price,hi_address,hi_room_count,hi_acreage,hi_house_unit," \
                  "hi_capacity,hi_beds,hi_deposit,hi_min_days,hi_max_days,up_name,up_avatar,hi_user_id " \
                  "from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id " \
                  "where hi_house_id=%(house_id)s"

            house_info = self.db.get(sql,house_id=house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="查询错误"))
        data = {
            "hid": house_id,
            "user_id": house_info["hi_user_id"],
            "title": house_info["hi_title"],
            "price": house_info["hi_price"],
            "address": house_info["hi_address"],
            "room_count": house_info["hi_room_count"],
            "acreage": house_info["hi_acreage"],
            "unit": house_info["hi_house_unit"],
            "capacity": house_info["hi_capacity"],
            "beds": house_info["hi_beds"],
            "deposit": house_info["hi_deposit"],
            "min_days": house_info["hi_min_days"],
            "max_days": house_info["hi_max_days"],
            "user_name": house_info["up_name"],
            "user_avatar": CONTENT.QINIU_IMAGE_LINK + "/" + house_info["up_avatar"] if house_info.get("up_avatar") else ""
        }
        # 查询房屋主页index图片
        sql = "select hi_index_image_url from ih_house_info where hi_house_id=%s"
        try:
            house_index_images = self.db.get(sql, house_id)
        except Exception as e:
            logging.error(e)
            house_index_images = None

        if house_index_images.get('hi_index_image_url','') == "FgeIOLVVP3K-nMyONdjkAIeKKRt5":
            try:
                house_index_images = self.db.get("select hi_url from ih_house_image where hi_house_id=%(house_id)s order by hi_ctime limit 1;",house_id=house_id)
            except Exception as e:
                logging.info(e)

            # if house_index_images == None:
            #     return self.write(dict(errno=RET.DATAERR,errmsg="图像上传错误"))

            index_image_key = house_index_images.get('hi_url', '')
            try:
                index_image = self.db.execute("update ih_house_info set hi_index_image_url=%(index_url)s where hi_house_id= %(house_id)s;"
                                               ,index_url=index_image_key,house_id=house_id)
            except Exception as e:
                logging.error(e)

        # 查询房屋的图片信息
        sql = "select hi_url from ih_house_image where hi_house_id=%s"
        try:
            house_images = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            house_images = None

        # 如果查询到的图片
        images = []
        if house_images:
            for image in house_images:
                images.append(CONTENT.QINIU_IMAGE_LINK+ "/" + image["hi_url"])
        data["images"] = images

        # 查询房屋的基本设施
        sql = "select hf_facility_id_list from ih_house_facility where hf_house_id=%s"
        try:
            house_facility = self.db.get(sql, house_id)
        except Exception as e:
            logging.error(e)
            house_facility = None

        # 如果查询到设施信息
        data["facilities"] = json.loads(house_facility["hf_facility_id_list"])

        # 查询评论信息
        sql = "select oi_comment,up_name,oi_utime,up_mobile from ih_order_info inner join ih_user_profile " \
              "on oi_user_id=up_user_id where oi_house_id=%s and oi_status=4 and oi_comment is not null"

        try:
            house_comment = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            house_comment = None
        comments = []

        if house_comment:
            for comment in house_comment:
                comments.append(dict(
                    user_name=comment["up_name"] if comment["up_name"] != comment["up_mobile"] else "匿名用户",
                    content=comment["oi_comment"],
                    ctime=comment["oi_utime"].strftime("%Y-%m-%d %H:%M:%S")
                ))
        data["comments"] = comments
        return self.write(dict(errno=RET.OK, errmsg="OK",data = data,user_id=user_id))



class HouseImageHandler(BaseHandler):
    """房屋图片上传"""
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

        # 将房屋图片key存入数据库
        try:
            update_image = self.db.execute("insert into ih_house_image(hi_house_id,hi_url) values(%(house_id)s, %(key)s);",house_id=house_id, key=key)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="房屋图片更新失败"))

        return self.write(dict(errno=RET.OK, errmsg="房屋图片保存成功", data=CONTENT.QINIU_IMAGE_LINK + '/' + key))

class HouseListHandler(BaseHandler):
    """get方式用来获取数据库数据，本身的逻辑不会对数据库数据产生影响"""
    @require_logined
    def get(self):

        # 获取参数
        start_date = self.get_argument("sd", "")
        end_date = self.get_argument("ed", "")
        area_id = self.get_argument("aid", "")
        sort_key = self.get_argument("sk", "new")
        page = self.get_argument("p", "1")

        # 检查参数
        # 判断日期格式、sort_Key 字段的值、page的整数

        # 数据查询
        # 涉及到表： ih_house_info 房屋的基本信息  ih_user_profile 房东的用户信息 ih_order_info 房屋订单数据
        sql = "select distinct hi_title,hi_house_id,hi_price,hi_room_count,hi_address,hi_order_count,up_avatar,hi_index_image_url,hi_ctime" \
              " from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id left join ih_order_info" \
              " on hi_house_id=oi_house_id"

        sql_total_count = "select count(distinct hi_house_id) count from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id " \
                          "left join ih_order_info on hi_house_id=oi_house_id"

        sql_where = []  # 用来保存sql语句的where条件
        sql_params = {}  # 用来保存sql查询所需的动态数据

        if start_date and end_date:
            sql_part = "((oi_begin_date>%(end_date)s or oi_end_date<%(start_date)s) " \
                       "or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
            sql_params["end_date"] = end_date
        elif start_date:
            sql_part = "(oi_end_date<%(start_date)s or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["start_date"] = start_date
        elif end_date:
            sql_part = "(oi_begin_date>%(end_date)s or (oi_begin_date is null and oi_end_date is null))"
            sql_where.append(sql_part)
            sql_params["end_date"] = end_date

        if area_id:
            sql_part = "hi_area_id=%(area_id)s"
            sql_where.append(sql_part)
            sql_params["area_id"] = area_id

        if sql_where:
            sql += " where "
            sql += " and ".join(sql_where)

        # 有了where条件，先查询总条目数
        try:
            ret = self.db.get(sql_total_count, **sql_params)
        except Exception as e:
            logging.error(e)
            total_page = -1
        else:
            total_page = int(math.ceil(ret["count"] / float(CONTENT.HOUSE_LIST_PAGE_CAPACITY)))
            page = int(page)
            if page > total_page:
                return self.write(dict(errno=RET.OK, errmsg="OK", data=[], total_page=total_page))

        # 排序
        if "new" == sort_key:  # 按最新上传时间排序
            sql += " order by hi_ctime desc"
        elif "booking" == sort_key:  # 最受欢迎
            sql += " order by hi_order_count desc"
        elif "price-inc" == sort_key:  # 价格由低到高
            sql += " order by hi_price asc"
        elif "price-des" == sort_key:  # 价格由高到低
            sql += " order by hi_price desc"

        # 分页
        # limit 10 返回前10条
        # limit 20,3 从20条开始，返回3条数据
        if 1 == page:
            sql += " limit %s" % CONTENT.HOUSE_LIST_PAGE_CAPACITY
        else:
            sql += " limit %s,%s" % (
            (page - 1) * CONTENT.HOUSE_LIST_PAGE_CAPACITY, CONTENT.HOUSE_LIST_PAGE_CAPACITY)

        logging.debug(sql)
        try:
            ret = self.db.query(sql, **sql_params)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="查询出错"))
        data = []
        if ret:
            for l in ret:
                house = dict(
                    house_id=l["hi_house_id"],
                    title=l["hi_title"],
                    price=l["hi_price"],
                    room_count=l["hi_room_count"],
                    address=l["hi_address"],
                    order_count=l["hi_order_count"],
                    avatar=CONTENT.QINIU_IMAGE_LINK + "/" + l["up_avatar"] if l.get("up_avatar") else "",
                    image_url=CONTENT.QINIU_IMAGE_LINK + "/" + l["hi_index_image_url"] if l.get(
                        "hi_index_image_url") else ""
                )
                data.append(house)

        self.write(dict(errno=RET.OK, errmsg="OK", data=data, total_page=total_page))