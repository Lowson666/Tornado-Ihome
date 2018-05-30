#coding:utf-8
from handlers import Port, VerifyCode

handlers = [
    (r'/',Port.IndexHandler),
    (r'/api/verifycode', VerifyCode.ImageCodeHandler)
]