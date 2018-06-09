# coding:utf-8
import json
import tornado.web

from tornado.web import RequestHandler
from libs.session import Seesion

class BaseHandler(RequestHandler):
    """Handler基类"""

    # 成员方法变成属性使用@property
    @property
    def db(self):
        return self.application.db

    @property
    def redis(self):
        return self.application.redis

    def initialize(self):
        pass

    def prepare(self):
        self.xsrf_token
        if self.request.headers.get("Content-Type","").startswith("application/json"):
            self.json_args = json.loads(self.request.body.decode('utf-8'))
        else:
            self.json_args = None

    def write_error(self, status_code, **kwargs):
        pass

    def set_default_headers(self):
        pass

    def on_finish(self):
        pass

    def get_current_user(self):
        self.seesion = Seesion(self)
        return self.seesion.data

class StaticFileHandler(tornado.web.StaticFileHandler):
    def __init__(self, *args, **kwargs):
        super(StaticFileHandler,self).__init__(*args, **kwargs)
        self.xsrf_token