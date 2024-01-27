# -*- coding: utf-8 -*-
"""
@Time    : 2023/2/24 11:40
@Author  : ghwg
@File    : WxPusher.py
wxpusher回调接口
"""
import json
from flask import Blueprint, request, session
from exts import limiter, csrf
from module.mysql.ModuleClass.IMEICodeClass import imei_class
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.ModuleClass.WxPusherClass import wxpusher_class

wxpusher_bp = Blueprint('wxpusher', __name__, url_prefix='/api')


# 微信回调接口
@wxpusher_bp.route('/wxpusher', methods=["POST", "GET"])
@limiter.exempt()
@csrf.exempt
def wxpusher_post():
    if request.method == 'POST':
        _data = json.loads(request.get_data())
        action = _data.get('action')  # 触发回调的方法
        if action == 'app_subscribe':  # 用户关注回调
            if (_data['data']).get("extra"):  # 带参数二维码关注回调
                """回调设置用户Uid"""
                wxpusher_class.set_wx_uid(_data)
                return "成功"
            else:  # 用户直接关注公众号回调
                return "忽略"
        elif action == 'send_up_cmd':  # 用户消息回调
            wxpusher_class.wxpusher_post_set_uid(_data)
            return "成功"
        else:
            return "未知回调"
    else:
        return "忽略"
