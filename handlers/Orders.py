# coding:utf-8
import logging
import hashlib
import config
import datetime
import json
import CONTENT

from libs.response_code import RET
from libs.login_verify import require_logined
from .BaseHandler import *

class OrderHandler(BaseHandler):
    """订单提交"""
    @require_logined
    def post(self):
        user_id = self.get_current_user()['user']
        house_id = self.json_args.get('house_id')
        order_start_date = self.json_args.get('start_date')
        order_end_date = self.json_args.get('end_date')
        # 参数检查
        if not all((house_id, order_start_date, order_end_date)):
            return self.write({"errno": RET.PARAMERR, "errmsg": "参数错误"})
        # 查询房屋是否存在
        try:
            house = self.db.get("select hi_price,hi_user_id from ih_house_info where hi_house_id=%s", house_id)
        except Exception as e:
            logging.error(e)
            return self.write({"errno": RET.DBERR, "errmsg": "房屋信息获取失败"})
        if not house:
            return self.write({"errno": RET.NODATA, "errmsg": "无数据"})
        # 预订的房屋是否是房东自己的
        if user_id == house["hi_user_id"]:
            return self.write({"errno": RET.ROLEERR, "errmsg": "用户禁止下单"})
        # 判断日期是否可以
        # order_start_date 与 order_end_date 两个参数是字符串，需要转为datetime类型进行比较
        # 比较order_start_date 是否 比 order_end_date 小
        days = (datetime.datetime.strptime(order_end_date, "%Y-%m-%d") - datetime.datetime.strptime(order_start_date,
                                                                                              "%Y-%m-%d")).days + 1
        if days <= 0:
            return self.write({"errno": RET.PARAMERR, "errmsg": "日期选择错误"})
        # 确保用户预订的时间内，房屋没有被别人下单
        try:
            ret = self.db.get("select count(*) counts from ih_order_info where oi_house_id=%(house_id)s "
                              "and oi_begin_date<%(end_date)s and oi_end_date>%(start_date)s",
                              house_id=house_id, end_date=order_end_date, start_date=order_start_date)
        except Exception as e:
            logging.error(e)
            return self.write({"errno": RET.DBERR, "errmsg": "数据获取错误"})
        if ret["counts"] > 0:
            return self.write({"errno": RET.DATAERR, "errmsg": "数据保存错误"})
        amount = days * house["hi_price"]
        try:
            # 保存订单数据ih_order_info，
            self.db.execute(
                "insert into ih_order_info(oi_user_id,oi_house_id,oi_begin_date,oi_end_date,oi_days,oi_house_price,oi_amount)"
                " values(%(user_id)s,%(house_id)s,%(begin_date)s,%(end_date)s,%(days)s,%(price)s,%(amount)s);"
                "update ih_house_info set hi_order_count=hi_order_count+1 where hi_house_id=%(house_id)s;",
                user_id=user_id, house_id=house_id, begin_date=order_start_date, end_date=order_end_date, days=days,
                price=house["hi_price"], amount=amount)
        except Exception as e:
            logging.error(e)
            return self.write({"errno": RET.DBERR, "errmsg": "数据保存错误"})
        self.write({"errno": RET.OK, "errmsg": "OK"})


class MyOrdersHandler(BaseHandler):

    @require_logined
    def get(self):
        user_id = self.get_current_user()['user']