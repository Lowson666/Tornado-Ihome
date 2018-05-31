# coding:utf-8

import logging
import random

from io import BytesIO
from captcha.image import ImageCaptcha
from handlers.BaseHandler import BaseHandler
from libs.response_code import RET
from CONTENT import *

class ImageCodeHandler(BaseHandler):
    """图片验证码"""
    def get(self):
        code_id = self.get_argument('codeid')
        pcode_id = self.get_argument('pcodeid')
        if pcode_id:
            try:
                self.redis.delete("")
            except Exception as e:
                logging.error(e)

        #创建图片验证码
        str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
        # 随机选取4个值作为验证码
        rand_str = ''
        for i in range(0, 4):
            rand_str += str1[random.randrange(0, len(str1))]
        image = ImageCaptcha()
        data = image.generate("%s" % rand_str)
        assert isinstance(data, BytesIO)
        # image.write('1234', 'out.png')

        try:
            self.redis.setex("image_code_%s"%code_id,IMAGE_CODE_EXCIST_TIME,rand_str)
        except Exception as e:
            logging.error(e)

        self.set_header("Content-Type","image/png")
        self.write(data.read())


class SMSCodeHandler(BaseHandler):
    """手机验证码"""
    def post(self):
        mobile = self.json_args.get("mobile")
        image_code_id = self.json_args.get("image_code_id")
        image_code_text = self.json_args.get("image_code_text")
        print(mobile,image_code_text,image_code_id)

        #判断验证码
        if not all((mobile,image_code_id,image_code_text)):
            return self.write(dict(errno=RET.PARAMERR,errmsg="参数错误"))

        try:
            real_image_code_text = self.redis.get("image_code_%s"%image_code_id).decode('utf-8')
        except Exception as e:
            return self.write(dict(errno=RET.DBERR,errmsg="查询错误"))

        if not real_image_code_text:
            return self.write(dict(errno=RET.NODATA,errmsg="验证码过期"))
        print(real_image_code_text)
        if real_image_code_text.lower() != image_code_text.lower():
            return self.write(dict(errno=RET.DATAERR,errmsg="验证码输入错误"))

        #验证码判断成功
        #生成随机验证码
        sms_code = "%04d" % random.randint(0,9999)
        try:
            self.redis.setex("sms_code_%s" % mobile,SMS_CODE_EXCIST_TIME,sms_code)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR,errmsg="生成信息验证码错误"))

        #发送短信
        try:

        self.write(dict(errno=RET.OK, errmsg="OK"))
