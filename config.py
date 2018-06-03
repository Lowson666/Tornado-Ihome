# coding:utf-8

import os

#aplication配置参数
settings = {
    "static_path": os.path.join(os.path.dirname(__file__),"static"),
    "tamplate_path": os.path.join(os.path.dirname(__file__),"template"),
    "cookie_secret": 'PhRtTCtjTeyMbr0jcf/S8Br61t88cE++rtktrcYDkmI=',
    "xsrf_cookies": True,
    "debug": True,
}

password_hash_key = 'dbdd87a8a25a4de0b096a63a620d9dcf'