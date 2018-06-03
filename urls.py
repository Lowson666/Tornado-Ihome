#coding:utf-8
import os

from handlers import Port, VerifyCode
from handlers.BaseHandler import StaticFileHandler
handlers = [
    #(r'/',Port.IndexHandler),
    (r'/api/smscode',VerifyCode.SMSCodeHandler),
    (r'/api/imagecode', VerifyCode.IMGCodeHandler),
    (r'/api/register', Port.RegiserHandler),
    (r'/api/login', Port.LoginHandler),
    (r'/api/check_login', Port.CheckLoginHandler),

    (r'/(.*)', StaticFileHandler,dict(path=os.path.join(os.path.dirname(__file__),"HTML"),default_filename="index.html")),
]