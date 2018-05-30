#coding:utf-8

import tornado.web
import tornado.ioloop
import tornado.options
import tornado.httpserver
import torndb
import redis
import os

from tornado.options import define,options
from config import settings
from urls import handlers


define('port',type=int,default=8000,help='run sever on the given port')


class Application(tornado.web.Application):
    """加入数据库和redis连接"""
    def __init__(self,*args,**kwargs):
        super(Application,self).__init__(*args,**kwargs)
        self.db = torndb.Connection(
            host="127.0.0.1",
            database="Ihome",
            user="root",
            password="123"
        )
        self.redis = redis.StrictRedis(
            host="127.0.0.1",
            port=6379
        )




def main():
    # 日志选项
    options.logging = 'debug'
    options.log_file_prefix = os.path.join(os.path.dirname(__file__),"logs/log")

    # 解析options描述
    tornado.options.parse_command_line()

    # 创建应用app
    app = Application(
        handlers,**settings
    )

    # 服务开启
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()