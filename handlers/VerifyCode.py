# coding:utf-8

import logging
import random
import re

from io import BytesIO
from captcha.image import ImageCaptcha
from handlers.BaseHandler import BaseHandler
from libs.response_code import RET
from libs.sms import send_sms
from CONTENT import *

class IMGCodeHandler(BaseHandler):
    """图片验证码"""
    def get(self):
        code_id = self.get_argument('codeid')
        pcode_id = self.get_argument('pcodeid')
        if pcode_id:
            try:
                self.redis.delete("image_code_%s"%pcode_id)
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


    # 判断验证码
        if not all([mobile,image_code_id,image_code_text]):
            return self.write(dict(errno=RET.PARAMERR,errmsg="参数错误"))
        # 判断手机是否正确
        if not re.match(r"1\d{10}",mobile):
            return self.write(dict(errno=RET.PARAMERR, errmsg="手机号错误"))
        # 查询redis中图片验证码内容
        try:
            real_image_code_text = self.redis.get("image_code_%s"%image_code_id).decode('utf-8')
        except Exception as e:
            return self.write(dict(errno=RET.DBERR,errmsg="查询错误"))
        if not real_image_code_text:
            return self.write(dict(errno=RET.NODATA,errmsg="验证码过期"))
        # 判断用户输入验证码是否正确
        if real_image_code_text.lower() != image_code_text.lower():
            return self.write(dict(errno=RET.DATAERR,errmsg="验证码输入错误"))

    # 验证码判断成功
        # 手机号是否存在检查
        sql = "select count(*) counts from ih_user_profile where up_mobile=%s"
        try:
            ret = self.db.get(sql, mobile)
        except Exception as e:
            logging.error(e)
        else:
            if 0 != ret["counts"]:
                return self.write(dict(errno=RET.DATAEXIST, errmsg="手机号已注册"))

        # 生成手机验证码
        sms_code = "%04d" % random.randint(0,9999)
        try:
            self.redis.setex("sms_code_%s" % mobile,SMS_CODE_EXCIST_TIME,sms_code)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR,errmsg="生成信息验证码错误"))

        # 发送短信
        try:
            sms_text = "您的验证码是：%s。请不要把验证码泄露给其他人。"% sms_code
            print(sms_text)
            result = send_sms(sms_text,mobile)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.THIRDERR, errmsg="验证码发送失败"))
        self.write(dict(errno=RET.OK, errmsg="OK"))
