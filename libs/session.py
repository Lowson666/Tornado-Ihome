# coding:utf-8
import uuid
import redis
import logging
import json
import CONTENT
import redis


class Seesion(object):
    """"""
    def __init__(self,request_handler):
        # self.redis = redis.StrictRedis(
        #     host="127.0.0.1",
        #     port=6379
        # )
        self.request_handler = request_handler
        self.session_id = self.request_handler.get_secure_cookie("session_id")
        if self.session_id:
            try:
                self.session_id = self.session_id.decode("utf-8")
            except  Exception as e:
                logging.error(e)

        if not self.session_id:
            # 用户第一次访问
            # 生成一个session_id，全局唯一
            self.session_id = uuid.uuid4().hex
            self.data = {}
        else:
            # 拿到了seesion_id，到redis中读取
            try:
                data = self.request_handler.redis.get("sess_%s" % self.session_id)

            except Exception as e:
                logging.error(e)
                self.data = {}
            if not data:
                self.data = {}
            else:
                self.data = json.loads(data.decode("utf-8"))


    # 保存session信息
    def save(self):
        json_data = json.dumps(self.data)
        try:
            self.request_handler.redis.setex("sess_%s" % self.session_id,CONTENT.SESSION_EXCIST_TIME,json_data)
        except Exception as e:
            logging.error(e)
            raise Exception("session save faild")
        else:
            self.request_handler.set_secure_cookie("session_id",self.session_id)

    # 清除session信息
    def clear(self):
        self.request_handler.clear_cookie("seesion_id")
        try:
            self.request_handler.redis.delete("sess_%s" % self.session_id)
        except Exception as e:
            logging.error(e)

