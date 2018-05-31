# coding:utf-8

import os

#aplication配置参数
settings = {
    "static_path": os.path.join(os.path.dirname(__file__),"static"),
    "tamplate_path": os.path.join(os.path.dirname(__file__),"template"),
    "cookie_secret": 'PhRtTCtjTeyMbr0jcf/S8Br61t88cE++rtktrcYDkmI=',
    "xsrf_cookies": False,
    "debug": True,
}

