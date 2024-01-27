# -*- coding: utf-8 -*-
"""
@Time    : 2023/2/24 8:46
@Author  : ghwg
@File    : Agent.py
网站代理蓝图
"""
import json
import re

from flask import Blueprint, session, render_template, request

from exts import limiter, csrf
from module.Check import login_check, agent_check
from module.blueprint.Forms import AddAgent
from module.mods import has_punctuation, has_chinese
from module.mysql.ModuleClass.AgentClass import agent_class
from module.mysql.ModuleClass.IMEICodeClass import imei_class
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.ModuleClass.WebClass import web_class

agent_bp = Blueprint('agent', __name__)


# 代理网站首页index
@agent_bp.route('/', subdomain='<subdomain>', methods=["GET"])
@limiter.exempt()
@csrf.exempt
def web_index(subdomain):
    """通过key返回代理网站配置"""
    web_info = agent_class.key_get_web_info(subdomain)
    """获取全局网站配置"""
    web_config = web_class.get_web_config()
    if web_info and web_config:
        session["web_key"] = subdomain  # 把subdomain保存到session中
        """获取网站配置"""
        web_info.update({"WebConfig": web_config})
        return render_template('user/pag/agent/index.html', **web_info)
    else:
        return render_template('404.html')
        # print(subdomain)
        # return {"a": subdomain, "b": request.host_url}


# 代理网站设置
@agent_bp.route('/SetAgentWebInfo', methods=["GET", "POST"])
@limiter.exempt()
@login_check
@agent_check
def set_web_info():
    # 获取session信息
    username = session.get("username")  # 用户名
    if request.method == "GET":
        # 获取代理网站配置
        info = agent_class.get_web_info(username)

        return render_template('user/pag/agent/WebInfoSet.html', **info)
    else:
        """获取post信息"""
        post_data = request.form.to_dict()
        try:
            WebName = post_data["WebName"]
            WebKey = post_data["WebKey"]
            Kfqq = post_data["Kfqq"]
            WebGG = post_data["WebGG"]
            QQGroup = post_data["QQGroup"]

        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """格式判断"""
            if len(WebKey) > 6:
                return {"code": 400, "msg": "二级域名前缀过长"}
            elif has_punctuation(WebKey):
                return {"code": 400, "msg": "代理域名中不能含有特殊符号"}
            elif has_chinese(WebKey):
                return {"code": 400, "msg": "代理域名中不能含有中文"}
            else:
                """构建字典"""
                info = {
                    "WebName": WebName,
                    "WebKey": WebKey,
                    "Kfqq": Kfqq,
                    "WebGG": WebGG,
                    "QQGroup": QQGroup,
                }
                """空值判断"""
                if info['WebName'] == "" or info['WebKey'] == "":
                    return {"code": 500, "msg": "参数为空值, 请填写参数提交"}
                else:
                    return agent_class.set_web_info(username, info)


# 更新跑步时间
@agent_bp.route('/PutRunTime', methods=['GET', 'POST'])
@csrf.exempt
def put_run_time():
    if request.method == 'GET':
        return render_template('user/pag/agent/PutRunTime.html')
    else:
        post_data = request.form.to_dict()  # post请求信息
        try:
            # 获取post请求信息
            IMEICode = post_data['IMEICode']  # IMEICode
            RunTime = post_data['RunTime']  # 跑步时间
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """检查格式"""
            if bool((re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')).match(RunTime)):
                return imei_class.put_imei_runtime(IMEICode, RunTime)
            else:
                return {"code": 400, "msg": "你输入的跑步时间格式不对"}


# 添加代理用户
@agent_bp.route("/AddAgent", methods=["GET", "POST"])
@limiter.exempt()
@login_check
@agent_check
def add_agent():
    """获取session信息"""
    UserName = session.get("username")
    UserLib = session.get("UserLib")
    if request.method == "GET":
        """获取代理额度"""
        AgentQuota = agent_class.get_agent_quota(UserName)
        info = {
            "AgentQuota": AgentQuota,
        }
        return render_template("user/pag/agent/AddAgent.html", **info)
    else:
        form = AddAgent(request.form)
        if form.validate():
            """获取post信息"""
            _post = request.form.to_dict()
            try:
                AgentUserName = _post['UserName']
                Password = _post['Password']
                QQh = _post['QQh']
                Email = _post['Email']
                """处理上级用户"""
                if UserLib == "管理员":
                    AdminUser = _post['AdminUser']  # 获取上级用户
                else:
                    AdminUser = UserName  # 默认是登录的网站用户
            except KeyError:
                return {"code": 500, "msg": "参数有误"}
            else:
                """构造字典"""
                info = {
                    "UserName": AgentUserName,
                    "Password": Password,
                    "QQh": QQh,
                    "Email": Email,
                    "AdminUser": AdminUser,
                }
                return agent_class.add_agent(info)
        else:
            errors = {field.name: field.errors for field in form if field.errors}
            return {"code": 400, "errors": errors}


# 代理列表
@agent_bp.route("/AgentList", methods=["GET", "POST"])
@limiter.exempt()
@login_check
@agent_check
def agent_user_list():
    """获取session信息"""
    UserName = session.get("username")  # 用户名
    if request.method == "GET":
        return render_template("user/pag/agent/AgentList.html")
    else:
        """获取post信息"""
        _post = json.loads(request.data)
        try:
            page = _post["page"]
            offset = _post["offset"]
            limit = _post["limit"]
            search = _post["search"]
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """切片处理账号数据"""
            users_list = agent_class.get_agent_list(UserName, search)
            users_list['rows'] = users_list['rows'][int(offset):int(limit) * int(page)]
            return users_list


# 修改代理信息
@agent_bp.route('/SetAgentInfo', methods=['GET', 'POST'])
@login_check
@agent_check
@limiter.exempt()
def set_agent_info():
    """获取session信息"""
    AdminUser = session.get("username")  # 上级账号
    AdminLib = user_class.get_user_lib(AdminUser)  # 上级的身份
    """获取代理账号"""
    if request.method == 'GET':
        """获取get参数"""
        UserName = request.args.get('UserName')  # 获取代理账号
        info = agent_class.get_agent_info(UserName, AdminUser)  # 获取代理信息
        info.update({"AdminLib": AdminLib})   # 上级身份加入
        return render_template('user/pag/agent/SetAgentInfo.html', **info)
    else:
        """获取post信息"""
        _post = request.form.to_dict()
        try:
            UserName = _post['user_name']
            info = {
                "QQh": _post["qqh"],
            }
            if _post["email"]:  # 填写邮箱了
                info.update({"Email": _post["email"]})
            else:
                info.update({"Email": None})
            if _post["wxuid"]:  # 填写微信订阅uid了
                info.update({"WxUid": _post["wxuid"]})
            else:
                info.update({"WxUid": None})
            if AdminLib == "管理员":
                info.update({"AgentQuota": _post["agent_quota"], "Password": _post["password"]})
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """修改数据库信息"""
            return agent_class.put_agent_info_agent(UserName, info, AdminUser)


