# -*- coding: utf-8 -*-
"""
@Time    : 2022/12/11 9:18
@Author  : ghwg
@File    : IMEICode.py

"""
import json

from flask import Blueprint, request, render_template, session, jsonify, url_for

from exts import limiter, csrf
from module.Check import login_check
from module.blueprint.Forms import UserAddIMEICode
from module.mods import mod_run_time, check_email
from module.mysql.ModuleClass.AgentClass import agent_class
from module.mysql.ModuleClass.IMEICodeClass import imei_class
from module.mysql.ModuleClass.KaMiClass import kami_class
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.ModuleClass.WebClass import web_class
from module.mysql.ModuleClass.WxPusherClass import wxpusher_class
from module.send import wx_qrcimg
from tasks.Run import user_run

user_imei_bp = Blueprint('user_imei', __name__, url_prefix='/User')


# 用户添加imei
@user_imei_bp.route('/AddIMEICode', methods=['GET', 'POST'])
@limiter.exempt()
@login_check
def user_add_imeicode():
    User = session.get('username')  # 用户名
    if request.method == 'GET':
        """获取cookie信息"""
        UserName = session.get('username')
        """获取用户信息"""
        user_info = user_class.get_user_info(UserName)
        return render_template('user/pag/imei/AddIMEICode.html', **user_info)
    else:
        form = UserAddIMEICode(request.form)
        if form.validate():
            _post = request.form.to_dict()  # 获取post信息
            try:
                IMEICode = _post['IMEICode']  # imeicode
                Email = _post['Email']  # 邮箱
                RunTime = mod_run_time(_post['run_time'])  # 跑步时间
                WxUid = _post['WxUid']  # wxpusher 用户id
            except KeyError:
                return {"code": 500, "msg": "参数有误"}
            else:
                info = {
                    "IMEICode": IMEICode,
                    "User": User,
                    "RunTime": RunTime,
                }
                if Email:  # 填邮箱了
                    info.update({"Email": Email})
                return imei_class.user_add_imei(info)
        else:
            errors = {field.name: field.errors for field in form if field.errors}
            return {"code": 400, "errors": errors}


# 代理网站首页添加IMEICode
@user_imei_bp.route("/Agent/Add/IMEICode", methods=["POST"])
@limiter.exempt()
@csrf.exempt
def agent_add_imei():
    """获取WebKey"""
    WebKey = session.get("web_key")
    """通过WebKey获取信息"""
    agent_data = agent_class.key_get_web_info(WebKey)  # 代理网站信息
    if agent_data:
        AgentUser = agent_data["AgentUser"]  # 代理账号
        """获取post参数"""
        post_data = request.form.to_dict()
        try:
            IMEICode = post_data["IMEICode"]
            RunTime = post_data["RunTime"]
            Kami = post_data["Kami"]
        except KeyError:
            return {"code": 500, "msg": "参数有误！"}
        else:
            if Kami:  # 输入卡密了->使用卡密
                """构造字典"""
                info = {
                    "WebKey": WebKey,
                    "Kami": Kami,
                    "Token": IMEICode,
                }
                kami_class.agent_use_kami(info)

            """构造字典"""
            info = {
                "IMEICode": IMEICode,
                "RunTime": RunTime,
                "User": AgentUser,
            }
            add_data = imei_class.user_add_imei(info)
            if add_data["code"] == 202:  # vip无效
                add_data.update({"msg2": "你的账号还未授权，接下来请输入卡密后提交"})
            if add_data['code'] == 200 or add_data['code'] == 203:  # 添加成功 -> 返回绑定微信公众号通知的消息文本
                """获取网站配置"""
                WxAppId = web_class.get_web_config()["WxAppId"]
                UserId = add_data["userid"]  # 阳光跑用户id
                """获取wxpusheruid"""
                if not wxpusher_class.userid_get_wxpusheruid(UserId):  # 如果系统中没有用户的wxpusheruid
                    """生成参数二维码"""
                    img_data = wx_qrcimg("userid", UserId)  # 绑定userid二维码地址
                    if img_data["code"] == 200:
                        img_url = img_data["img"]
                    else:
                        img_url = f"{url_for('static', filename='images/loading-logo.png')}"
                    add_data.update({"wxpusher": {"code": f"#{WxAppId} {UserId}", "img": img_url}})
                else:
                    pass
            return add_data
    else:
        return {"code": 500, "msg": "异常请求接口"}


# imei列表
@user_imei_bp.route('/IMEICodeList', methods=['GET', 'POST'])
@login_check
@limiter.exempt()
def user_imei_list():
    """获取代理账号信息"""
    UserName = session.get("username")
    if request.method == "GET":
        return render_template("user/pag/imei/IMEICodeList.html")
    else:  # post获取账号列表
        """获取post信息"""
        _post = json.loads(request.data)
        try:
            search = _post.get('search')
            page = _post["page"]
            offset = _post["offset"]
            limit = _post['limit']
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """切片处理账号数据"""
            imei_list = imei_class.get_imei_list(UserName, search)
            imei_list['rows'] = imei_list['rows'][int(offset):int(limit) * int(page)]
            return imei_list


# 修改IMEICode用户信息
@user_imei_bp.route('/SetIMEICodeInfo', methods=['GET', 'POST'])
@login_check
@limiter.exempt()
def set_imei_info():
    """获取代理账号"""
    UserName = session.get("username")
    if request.method == 'GET':
        """获取get参数"""
        userid = request.args.get('UserId')  # 阳光跑userid
        info = imei_class.get_imei_info(UserName, userid)  # 获取imei信息
        return render_template('user/pag/imei/SetIMEICodeInfo.html', **info)
    else:
        """获取post信息"""
        _post = request.form.to_dict()
        try:
            info = {
                "IMEICode": _post["IMEICode"],
                "UserId": _post["userid"],
                "State": _post["state"],
                "RunTime": mod_run_time(_post["run_time"]),
                "Email": _post.get("email"),
                "User": _post.get("user"),
            }
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """修改数据库信息"""
            return imei_class.set_imei_info(UserName, info)


# 删除IMEICode
@user_imei_bp.route('/DelIMEICodeInfo', methods=['POST'])
@login_check
@limiter.exempt()
def del_imei_info():
    """获取代理信息"""
    UserName = session.get("username")
    DelUserIdList = []  # 删除的跑步账号列表
    """获取post参数"""
    try:
        _post = request.form.to_dict()
        try:
            DelUserIdList = _post['UserId'].split(',')
        except IndexError:  # 单删
            DelUserIdList.append(request.form.get("UserId"))
    except KeyError:
        return {"code": 500, "msg": "参数有误"}
    else:
        return imei_class.del_imei(UserName, DelUserIdList)  # 删除IMEICode


# 用户后台执行跑步
@user_imei_bp.route('/UserRunIMEI', methods=['POST'])
@login_check
@limiter.exempt()
def user_run_imei():
    UserIdRunList = []  # 跑步列表
    """获取cookie信息"""
    UserName = session.get('username')  # 用户名
    """获取post信息"""
    _post = request.form.get('UserId')
    if _post:
        return_msg = ''  # 返回的信息
        UserIdRunList = _post.split(',')
        for UserId in UserIdRunList:  # 循环执行跑步
            run_data = user_run(UserName, UserId)  # 跑步结果
            if run_data['code'] == 200:  # 跑步成功
                return_msg += f'<a style="color: green">{run_data["msg"]}</a><br>'
            else:  # 异常情况
                return_msg += f'<a style="color: red">{run_data["msg"]}</a><br>'
        return {"code": 200, "msg": return_msg}
    else:
        return {"code": 500, "msg": "参数有误"}


