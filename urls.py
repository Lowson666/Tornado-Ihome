#coding:utf-8
import os

from handlers import Port, VerifyCode
from tornado.web import StaticFileHandler
handlers = [
    #(r'/',Port.IndexHandler),
    (r'/api/smscode',VerifyCode.SMSCodeHandler),
    (r'/api/imagecode', VerifyCode.ImageCodeHandler),
    (r'/(.*)', StaticFileHandler,dict(path=os.path.join(os.path.dirname(__file__),"HTML"),default_filename="index.html")),
]