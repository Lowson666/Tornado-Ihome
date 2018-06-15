#coding:utf-8
import os

from handlers import Port, VerifyCode, Profile, House
from handlers.BaseHandler import StaticFileHandler
handlers = [
    #(r'/',Port.IndexHandler),
    (r'/api/smscode',VerifyCode.SMSCodeHandler),
    (r'/api/imagecode', VerifyCode.IMGCodeHandler),
    (r'/api/register', Port.RegiserHandler),
    (r'/api/login', Port.LoginHandler),
    (r'/api/check_login', Port.CheckLoginHandler),
    (r'/api/logout', Port.LogoutHandler),

    (r'/api/profile', Profile.ProfileHandler),
    (r'/api/profile/name', Profile.ProfilenameHandler),
    (r'/api/profile/avatar', Profile.ProfileavatarHandler),
    (r'/api/profile/auth', Profile.ProfileauthHandler),

    (r'/api/house/index', House.HouseindexHandler),
    (r'/api/house/my', House.MyhouseHandler),
    (r'/api/house/area', House.HouseareaHandler),
    (r'/api/house/info', House.HouseinfoHandler),
    (r'/api/house/image', House.HouseimageHandler),

    (r'/(.*)', StaticFileHandler,dict(path=os.path.join(os.path.dirname(__file__),"HTML"),default_filename="index.html")),
]