# coding:utf-8
import logging
from captcha.image import ImageCaptcha
from io import BytesIO
from .BaseHandler import BaseHandler


class ImageCodeHandler(BaseHandler):
    def get(self):
        # code_id = self.get_argument("codeid")
        # pre_code_id = self.get_argument("pcodeid")
        # if pre_code_id:
        #     try:
        #         self.redis.delete("")
        #     except Exception as e:
        #         logging.error(e)


        image = ImageCaptcha()
        data = image.generate("1234")
        assert isinstance(data, BytesIO)
        # image.write('1234', 'out.png')
        self.set_header("Content-Type","image/png")
        self.write(data.read())

