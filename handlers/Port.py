# coding:utf-8
from .BaseHandler import *


class IndexHandler(BaseHandler):
    def get(self):
        # 使用@propertys可以直接把成员方法当成属性使用
        # self.db
        # self.redis
        self.write('hellow!')