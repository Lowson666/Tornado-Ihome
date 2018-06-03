# coding:utf-8
import uuid
import redis
import logging
import json
import CONTENT

class Seesion(object):
    """"""
    def __init__(self,request_handler):
        self.request_handler = request_handler
        self.session_id = self.request_handler.get_secure_cookie("session_id")
        if not self.session_id:
            # 用户第一次访问
            # 生成一个session_id，全局唯一
            self.session_id = uuid.uuid4().hex
            self.data = {}
        else:
            # 拿到了seesion_id，到redis中读取
            try:
                data = self.redis.get("sess_%s" % self.session_id)
            except Exception as e:
                logging.error(e)
                self.data = {}
            if not data:
                self.data = {}
            else:
                self.data = json.loads(data)

    # 保存session信息
    def save(self):
        json_data = json.dumps(self.data)
        try:
            self.redis.setex("sess_%s" % self.session_id,CONTENT.SESSION_EXCIST_TIME,json_data)
        except Exception as e:
            logging.error(e)
            raise Exception("session save faild")
        else:
            self.request_handler.set_secure_cookie("session_id",self.session_id)

    # 清除session信息
    def clear(self):
        self.request_handler.clear_cookie("seesion_id")
        try:
            self.redis.delete("sess_%s" % self.session_id)
        except Exception as e:
            logging.error(e)

