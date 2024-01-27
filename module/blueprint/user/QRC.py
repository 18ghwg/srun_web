# -*- coding: utf-8 -*-
"""
@Time    : 2022/12/13 19:44
@Author  : ghwg
@File    : QRC.py

"""
import re

from flask import Blueprint, request, render_template

from exts import limiter, csrf
from module.QrcLogin import get_qcr_img, check_login_state
from module.Check import login_check

user_qrc_bp = Blueprint('user_qrc', __name__, url_prefix='/User')


# 获取登录二维码
@user_qrc_bp.route('/QRC/GetImg', methods=['POST', 'GET'])
@limiter.exempt()
@csrf.exempt
def get_qrc_img():
    qrc_data = get_qcr_img()
    if qrc_data:  # 获取到了
        info = {"code": 200, "img_url": qrc_data.get('img_url'), "uuid": qrc_data.get('uuid')}
    else:
        info = {"code": 400, "img_url": "https://raw.githubusercontents.com/483913085/Annex/main/2.gif", "uuid": None}
    return info


# 查询扫码登录状态
@user_qrc_bp.route('/QRC/CheckLogin', methods=['POST'])
@limiter.exempt()
@csrf.exempt
def qrc_check_login():
    post_data = request.form.to_dict()
    try:
        qrc_img_url = post_data['qrc_img_url']  # 二维码链接
        uuid = post_data["uuid"]  # uuid
    except KeyError:
        return {"code": 500, "msg": "未能成功获取登录二维码参数"}
    else:
        login_state = check_login_state(uuid, "QrcLogin")  # 检测登录状态
        if isinstance(login_state, dict):  # 登陆成功 返回如果是AddVip不会对vip用户返回IMEICode
            return login_state
        else:  # 登陆失败
            info = {"code": 500, "msg": "未登录！"}
            return info
