# coding:utf-8
import logging
import CONTENT
import hashlib
import config
import re

from libs.response_code import RET
from libs.qiniu_image_storage import storage
from libs.login_verify import require_logined
from .BaseHandler import *


class ProfileHandler(BaseHandler):
    """个人信息页面信息调取"""
    @require_logined
    def get(self):

        user_id = self.get_current_user()['user']

        # 获取名字，电话号码，头像图片链接
        try:
            ret = self.db.get("select up_name,up_mobile,up_avatar from ih_user_profile where up_user_id=%s;", user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errno": RET.DBERR, "errmsg": "get data error"})

        if ret["up_avatar"]:
            img_url = CONTENT.QINIU_IMAGE_LINK +'/' + ret["up_avatar"]
        else:
            img_url = ""
        return self.write({"errno": RET.OK, "errmsg": "OK",
                    "data": {"user_id": user_id, "name": ret["up_name"], "mobile": ret["up_mobile"],
                             "avatar": img_url}})



class ProfileAvatarHandler(BaseHandler):
    """用户头像上传处理"""

    @require_logined
    def post(self):
        user_id = self.get_current_user()['user']
        # 获取用户上传头像数据
        try:
            avatar_data = self.request.files['avatar'][0]['body']
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DATAERR, errmsg="头像上传失败"))

        # 将数据上传到云空间，取得文件名key
        try:
            # 将头像数据上传到七牛云
            key = storage(avatar_data)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DATAERR, errmsg="头像上传云端失败"))

        # 将头像key存入数据库
        try:
            update_avatar = self.db.execute("update ih_user_profile set up_avatar=%(key)s where up_user_id=%(user_id)s ;",key = key,user_id = user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="头像更新失败"))
        return self.write(dict(errno=RET.OK, errmsg="头像保存成功",data=CONTENT.QINIU_IMAGE_LINK +'/'+key))



class ProfileNameHandler(BaseHandler):
    """用户名字修改上传处理"""

    @require_logined
    def post(self):
        name = self.json_args.get('name')
        user_id = self.get_current_user()['user']
        try:
            update_name = self.db.execute("update ih_user_profile set up_name = %(name)s where up_user_id=%(user_id)s;", name=name,user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="名称修改失败"))
        return self.write(dict(errno=RET.OK, errmsg="修改成功"))



class ProfileAuthHandler(BaseHandler):
    """用户身份证信息上传处理"""

    @require_logined
    def get(self):
        # 获取该用户ID
        user_id = self.get_current_user()['user']
        # 从数据库查询该用户身份信息
        try:
            ID_name = self.db.get("select up_real_name,up_id_card from ih_user_profile where up_user_id=%s;", user_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errno": RET.DBERR, "errmsg": "数据错误"})
        return self.write(dict(errno=RET.OK, errmsg="查询成功",data={"real_name":ID_name.get("up_real_name",''),"id_card":ID_name.get("up_id_card",'')}))

    # 初始设置用户身份信息，信息设置后不能修改
    @require_logined
    def post(self):
        # 获取该用户ID，上传的身份证和名字
        user_id = self.get_current_user()['user']
        ID = self.json_args.get('id_card')
        ID_name = self.json_args.get('real_name')

        # 将该用户上传的身份证和名字存入数据库
        try:
            update_auth = self.db.execute("update ih_user_profile set up_real_name=%(name)s,up_id_card=%(ID)s where up_user_id=%(user_id)s ;",name=ID_name, ID=ID,user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errno=RET.DBERR, errmsg="名称修改失败"))
        return self.write(dict(errno=RET.OK, errmsg="修改成功"))
