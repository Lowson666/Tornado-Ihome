# coding:utf-8
import functools

from .response_code import RET

def require_logined(fun):
    @functools.wraps(fun)
    def wrapper(request_handler,*args,**kwargs):
        # 根据get_current_user方法判断用户是否登录
        a = request_handler.get_current_user()

        if request_handler.get_current_user():
            fun(request_handler,*args,**kwargs)
        else:
            return request_handler.write(dict(errno=RET.SESSIONERR, errmsg="用户未登录"))
    return wrapper
