# coding:utf-8
import logging

from .BaseHandler import *


class IndexHandler(BaseHandler):
    def get(self):
        # 添加日志信息
        # logging.debug('debug')
        # logging.info('info')
        # logging.warning('warning')
        # logging.error('error')
        # print('msg')
        # 使用@propertys可以直接把成员方法当成属性使用
        # self.db
        # self.redis
        self.write('hellow!')