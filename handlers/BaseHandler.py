# coding:utf-8

from tornado.web import RequestHandler


class BaseHandler(RequestHandler):
    """Handler基类"""

    #成员方法变成属性使用@property
    @property
    def db(self):
        return self.application.db

    @property
    def redis(self):
        return self.application.redis

    def initialize(self):
        pass

    def prepare(self):
        pass

    def write_error(self, status_code, **kwargs):
        pass

    def set_default_headers(self):
        pass

    def on_finish(self):
        pass