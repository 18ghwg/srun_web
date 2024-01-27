# -*- coding: utf-8 -*-
"""
@Time    : 2022/12/26 20:57
@Author  : ghwg
@File    : Kami.py
卡密接口蓝图文件
"""
import json

from flask import Blueprint, request, session, render_template

from exts import limiter, csrf
from module.Check import login_check, admin_check, agent_check
from module.mysql.ModuleClass.KaMiClass import kami_class
from module.mysql.ModuleClass.VipClass import vip_class

user_kami_bp = Blueprint('user_kami', __name__, url_prefix='/User')


# 已使用卡密列表
@user_kami_bp.route('/Kami/UseList', methods=['GET', 'POST'])
@login_check
@limiter.exempt()
def use_kami_list():
    """获取cookie信息"""
    UserName = session.get('username')
    if request.method == 'GET':
        return render_template('user/pag/kami/UsekamiList.html')
    else:
        """获取post参数"""
        _post = json.loads(request.data)
        try:
            page = _post['page']  # 页码
            offset = _post['offset']  # 数据起始位置
            limit = _post['limit']
            search = _post.get('search')  # 搜索的关键词
        except KeyError:
            return {"code": 500, "msg": "参数错误"}
        else:
            kami_list = kami_class.get_user_use_kami_list(UserName, search)  # 获取已使用卡密列表
            """数据切片"""
            kami_list['rows'] = kami_list['rows'][int(offset):int(limit) * int(page)]
            return kami_list


# 未使用卡密列表
@user_kami_bp.route('/Kami/NUseList', methods=['GET', 'POST'])
@login_check
@limiter.exempt()
def nuse_kami_list():
    """获取cookie信息"""
    UserName = session.get('username')
    if request.method == 'GET':
        return render_template('user/pag/kami/NUsekamiList.html')
    else:
        """获取post参数"""
        _post = json.loads(request.data)
        try:
            page = _post['page']  # 页码
            offset = _post['offset']  # 数据起始位置
            limit = _post['limit']
            search = _post.get('search')  # 搜索关键词
        except KeyError:
            return {"code": 500, "msg": "参数错误"}
        else:
            kami_list = kami_class.get_user_nuse_kami_list(UserName, search)  # 获取未使用卡密列表
            """数据切片"""
            kami_list['rows'] = kami_list['rows'][int(offset):int(limit) * int(page)]
            return kami_list


# 卡密生成
@user_kami_bp.route('/Kami/Add', methods=['POST', 'GET'])
@login_check
@admin_check
@limiter.exempt()
def add_kami():
    # 获取cookie信息
    if request.method == 'GET':
        # 获取vip类型列表
        kami_lib_list = vip_class.get_vip_lib_list()
        info = {
            "kami_lib_list": kami_lib_list
        }
        return render_template('user/pag/kami/AddKami.html', **info)
    else:
        # 获取post信息
        _post = request.form.to_dict()
        try:
            KamiLib = _post["kami_lib"]
            KamiNum = _post["kami_num"]
            KamiDay = _post["kami_day"]
            num = int(_post["num"])
            SCUser = _post["SCUser"]
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            kami_info = {
                "KamiLib": KamiLib,
                "Day": KamiDay,
                "Num": KamiNum,
                "SCUser": SCUser,
            }
            return {"code": 200, "msg": "生成成功", "data": {"kami": kami_class.sc_kamis(num, kami_info)}}


# 代理首页使用卡密添加vip
@user_kami_bp.route("/Kami/Agent/Use", methods=["POST"])
@csrf.exempt
def agent_user_kami():
    """获取post参数"""
    post_data = request.form.to_dict()
    try:
        Token = post_data["Token"]
        Kami = post_data["Kami"]
    except KeyError:
        return {"code": 500, "msg": "参数有误"}
    else:
        """获取session中的WebKey"""
        WebKey = session.get("web_key")  # 通过webkey搜索代理账号，把vip账号添加到其名下
        """构造字典"""
        info = {
            "WebKey": WebKey,
            "Kami": Kami,
            "Token": Token,
        }
        return kami_class.agent_use_kami(info)


# 转移卡密
@user_kami_bp.route('/Kami/TranSfer', methods=['POST'])
@limiter.exempt()
@login_check
@agent_check
def kami_transfer():
    SendUser = session.get('username')  # 卡密发送者
    kami_list = request.json  # 接收转移卡密数据的列表数据[{}]
    if kami_list:
        return kami_class.kami_transfer(SendUser, kami_list)
    else:
        return {"code": 500, "msg": "参数为空"}
