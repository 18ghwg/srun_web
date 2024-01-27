# -*- coding: utf-8 -*-
"""
@Time    : 2022/12/13 18:17
@Author  : ghwg
@File    : Vip.py

"""
import json

from flask import Blueprint, request, render_template, session, redirect, url_for

from exts import limiter
from module.Check import login_check, admin_check
from module.QrcLogin import check_login_state
from module.mysql.ModuleClass.KaMiClass import kami_class
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.ModuleClass.VipClass import vip_class
from module.mysql.ModuleClass.WebClass import web_class
from module.srun_token import get_imei_info

user_vip_bp = Blueprint('user_vip', __name__, url_prefix='/User')


# 添加/续费Vip
@user_vip_bp.route('/Vip/Add', methods=['GET', 'POST'])
@limiter.limit("30/day")
@login_check
def user_add_vip():
    """获取cookie信息"""
    UserName = session.get('username')
    if request.method == "GET":
        AdminUserLib = user_class.get_admin_userlib(UserName).get("Lib")  # 上级用户身份
        if AdminUserLib == "管理员":
            """获取网站配置"""
            web_config = web_class.get_web_config()
            info = {"KamiPayUrl": web_config.get("KamiPayUrl")}
        else:
            info = {}
        return render_template('user/pag/vip/AddVip.html', **info)
    else:
        """获取cookie信息"""
        UserName = session.get("username")  # 用户名
        """处理post信息"""
        post_data = request.form.to_dict()
        try:
            info = {
                "Kami": post_data['kami'],
                "Name": post_data['name'],
                "School": post_data['school'],
                "UserId": post_data['userid'],
            }
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """判断参数完整"""
            if info["Kami"] == '' or info["Kami"] == 'undefined' or \
                    info["Name"] == '' or info["Name"] == 'undefined' or \
                    info["School"] == '' or info["School"] == 'undefined' or \
                    info["UserId"] == '' or info["UserId"] == 'undefined':
                return {"code": 500, "msg": "请先登录后再填写卡密使用"}
            else:
                """添加/续费vip"""
                return vip_class.add_vip(UserName, info)  # 添加成功


# 查询扫码授权登录状态
@user_vip_bp.route('/Vip/QRC/CheckLogin', methods=['POST'])
@limiter.exempt()
@login_check
def qrc_check_login():
    post_data = request.form.to_dict()
    try:
        qrc_img_url = post_data['qrc_img_url']  # 二维码链接
        uuid = post_data["uuid"]  # uuid
    except KeyError:
        return {"code": 500, "msg": "二维码地址未获取到, 请换个环境打开本站"}
    else:
        login_state = check_login_state(uuid, "AddVip")  # 检测登录状态
        if isinstance(login_state, dict):  # 请求成功，返回请求状态码如果code是405则返回用户信息否则返回code和msg
            return login_state
        else:  # 登陆失败
            info = {"code": 500, "msg": "未登录！"}
            return info


# imei登录
@user_vip_bp.route("/Vip/IMEICode/CheckLogin", methods=["POST"])
@limiter.exempt()
@login_check
def imei_check_login():
    post_data = request.form.to_dict()
    try:
        IMEICode = post_data["IMEICode"]
    except ValueError:
        return {"code": 500, "msg": "参数有误"}
    else:
        """阳光跑登录"""
        SrunInfo = get_imei_info(IMEICode)
        if isinstance(SrunInfo, dict):  # 获取信息成功
            """获取信息"""
            Name = SrunInfo.get("name")  # 姓名
            School = SrunInfo.get("school")  # 学校
            UserId = SrunInfo.get("userid")  # userid
            return {"code": 200, "msg": f"登录成功-你的信息："
                                        f"<br>姓名：{Name}"
                                        f"<br>学校：{School}"
                                        f"<br>UserId:{UserId}"
                                        f"<br>请继续输入卡密操作",
                    "name": Name,
                    "school": School,
                    "userid": UserId}
        else:
            return {"code": 400, "msg": "IMEICode无效"}


# vip列表
@user_vip_bp.route('/Vip/List', methods=['GET', 'POST'])
@limiter.exempt()
@login_check
def user_vip_list():
    """获取cookie信息"""
    UserName = session.get('username')
    if request.method == 'GET':
        return render_template('user/pag/vip/VipList.html')
    else:
        """获取post信息"""
        _post = json.loads(request.data)
        try:
            page = _post["page"]
            offset = _post["offset"]
            limit = _post['limit']
            search = _post.get('search')  # 搜索数据关键词
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """切片处理账号数据"""
            vip_list = vip_class.get_vip_list(UserName, search)
            vip_list['rows'] = vip_list['rows'][int(offset):int(limit) * int(page)]
            return vip_list


# 编辑vip信息
@user_vip_bp.route('/Vip/Set/Info', methods=["POST", "GET"])
@limiter.exempt()
@login_check
@admin_check
def set_vip_info():
    # 获取session信息
    username = session.get("username")  # 用户名
    if request.method == "GET":
        # 获取url参数
        UserId = request.args.get("UserId")  # 阳光跑用户id
        if UserId:
            # 获取VIP信息
            vip_info = vip_class.get_vip_info(UserId)

            if not vip_info:
                return redirect(url_for('page_not_found'))
            else:
                return render_template('user/pag/vip/SetVipInfo.html', **vip_info)
        else:  # UserId没有给
            return redirect(url_for('page_not_found'))
    else:  # post接口请求
        # 获取post参数
        _post = request.form.to_dict()
        try:
            UserId = _post['UserId']
            VipLib = _post['VipLib']
            VipRunNum = _post['VipRunNum']
            VipedDate = _post['VipedDate']
            AdminUser = _post.get('User')
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            # 构建字典
            info = {
                "UserId": UserId,
                "VipLib": VipLib,
                "VipRunNum": VipRunNum,
                "VipedDate": VipedDate,
                "User": AdminUser if AdminUser != "" else None,
            }
            # 修改表中数据
            return vip_class.set_vip_info(username, info)


# 删除Vip
@user_vip_bp.route('/Vip/Del', methods=['POST'])
@login_check
@limiter.exempt()
def del_vip():
    """获取代理信息"""
    UserName = session.get("username")
    """获取post参数"""
    _post = request.form.to_dict()
    try:
        UserId = _post["UserId"]
    except KeyError:
        return {"code": 500, "msg": "参数有误"}
    else:
        return vip_class.del_vip(UserName, UserId)  # 删除IMEICode


#  积分兑换vip
@user_vip_bp.route("/Vip/Credit", methods=['GET', 'POST'])
@login_check
def credit_vip():
    # 获取session数据
    username = session.get('username')  # 用户名
    if request.method == 'GET':
        # 获取用户积分余额
        user_credit = user_class.get_user_credit_num(username)
        info = {"UserCredit": user_credit}
        return render_template('user/pag/vip/CreditVip.html', **info)
    else:
        post_data = request.form.to_dict()  # 获取post数据
        try:
            KamiLib = post_data["kami_lib"]  # 卡密类型
            KamiDayNum = post_data["kami_day"]  # 卡密天数
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            # 构造字典数据
            info = {
                "UserName": username,
                "KamiLib": KamiLib,
                "KamiDayNum": KamiDayNum,
            }
            # 数据判断
            try:
                int(KamiDayNum)
            except ValueError:
                return {"code": 500, "msg": "参数有误"}
            else:
                if int(KamiDayNum) < 10:  # 兑换天数限制
                    return {"code": 400, "msg": "兑换天数限制：大于等于5天"}
                else:
                    return kami_class.credit_kami(info)
                    # return {"code": 400, "msg": "暂时关闭"}
