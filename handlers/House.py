# coding:utf-8
import logging
import hashlib
import config
import re
import CONTENT

from libs.response_code import RET
from .BaseHandler import *


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