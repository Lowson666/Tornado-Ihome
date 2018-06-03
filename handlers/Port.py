# coding:utf-8
import logging
import hashlib
import config

from libs.response_code import RET
from .BaseHandler import *


class RegiserHandler(BaseHandler):
    """注册"""
    def post(self):
        mobile = self.json_args.get("mobile")
        sms_code = self.json_args.get("phonecode")
        password = self.json_args.get("password")
        # 判断前端返回参数是否完善
        if not all([mobile,sms_code,password]):
            return self.write(dict(errno=RET.DATAERR, errmsg="参数错误"))
        # 检查手机验证码是否正确
        real_sms_code = self.redis.get("sms_code_%s" % mobile)

        if real_sms_code.decode("utf-8") != str(sms_code):
            return self.write(dict(errno=RET.DBERR, errmsg="验证码错误"))
        # 加密密码
        password = hashlib.sha256((config.password_hash_key + password).encode("utf-8")).hexdigest()
        # 数据库创建用户数据
        try:
            res = self.db.execute("INSERT INTO ih_user_profile(up_name,up_mobile,up_passwd) VALUES (%(name)s,%(moblie)s,%(passwd)s)",name = mobile, mobile = mobile, passwd = password)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DATAEXIST, errmsg="手机号已存在"))
        # 将数据存入session
        try:
            self.seesion = Seesion(self)
            self.seesion.data['user'] = res
            self.seesion.data['name'] = mobile
            self.seesion.data['mobile'] = mobile
            self.seesion.save()
        except Exception as e:
            logging.error(e)

        self.write(dict(errno=RET.OK, errmsg="OK"))

class LoginHandler(BaseHandler):
    """登录"""
    def post(self):
        mobile = self.json_args.get("mobile")
        password = self.json_args.get("password")

        if not all([mobile,password]):
            return self.write(dict(errno=RET.PARAMERR, errmsg="参数错误"))
        res = self.db.get("SELECT up_user_id,up_name,up_passwd FROM ih_user_profile WHERE up_mobile = %(mobile)s",mobile = mobile)
        password = hashlib.sha256(config.password_hash_key + password).hex

        print(res,res["up_passwd"],password)
        if res and res["up_passwd"] == unicode(password):
            try:
                self.seesion = Seesion(self)
                self.seesion.data['user'] = res
                self.seesion.data['name'] = mobile
                self.seesion.data['mobile'] = mobile
                self.seesion.save()
            except Exception as e:
                logging.error(e)
            return self.write(dict(errno=RET.OK, errmsg="OK"))
        else:
            return self.write(dict(errno=RET.NODATA, errmsg="手机帐号或密码错误"))



class CheckLoginHandler(BaseHandler):
    def get(self):
        if self.get_current_user():
            self.write(dict(errno = 0, errmsg= "true" ,data= dict(name=self.seesion.data.get("name"))))
        else:
            self.write(dict(errno=1, errmsg="false"))