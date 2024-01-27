# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/27 6:22
@Author  : ghwg
@File    : Workorder.py

"""
import json

from flask import Blueprint, session, request, render_template, jsonify

from exts import csrf, limiter
from module.Check import login_check
from module.blueprint.Forms import WorkorderAdd
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.ModuleClass.WorkorderClass import workorder_class

user_work_bp = Blueprint("user_work", __name__, url_prefix="/User")


# 工单列表
@user_work_bp.route("/Workorder/List", methods=["GET", "POST"])
@login_check
def workorder_list():
    """获取cookie信息"""
    UserName = session.get('username')
    if request.method == 'GET':
        return render_template('user/pag/workorder/WorkList.html')
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
            _work_list = workorder_class.get_workorder_list(UserName, search)
            _work_list['rows'] = _work_list['rows'][int(offset):int(limit) * int(page)]
            return _work_list


# 聊天界面
@user_work_bp.route('/Workorder/Chat', methods=['GET'])
@login_check
def chat():
    """获取GET工单ID"""
    get_data = request.args.to_dict()
    try:
        workorder_id = get_data["WorkorderID"]
    except KeyError:
        return render_template("erro.html", **{"code": 500, "msg": "工单参数有误"})
    else:
        if not bool(workorder_id):
            return render_template("erro.html", **{"code": 500, "msg": "工单参数有误"})
        else:
            return render_template('user/pag/workorder/Chat.html', **{"WorkorderID": workorder_id})


# 获取消息数据
@user_work_bp.route('/Workorder/Chat/Get/Msg', methods=['GET', 'POST'])
@csrf.exempt
@login_check
@limiter.limit("1/2seconds")
def chat_get_msg():
    username = session.get('username')  # 请求数据的账号
    if request.method == "POST":
        """获取post数据"""
        request_data = json.loads(request.data)
    elif request.method == "GET":
        request_data = request.args.to_dict()
    else:
        return render_template("erro.html", **{"code": 500, "msg": "无效请求！"})
    try:
        workorder_id = request_data['workorder_id']
    except KeyError:
        return {"code": 200, "data": [], "msg": "参数有误"}
    else:
        return workorder_class.get_msg_data(username, workorder_id)


# 回复工单
@user_work_bp.route('/Chat/Send/Msg', methods=['POST'])
@login_check
@csrf.exempt
def chat_send_msg():
    username = session.get('username')  # 用户名
    """获取POST数据"""
    print(request.data)
    post_data = json.loads(request.data)
    print(post_data)
    try:
        workorder_id = post_data['workorder_id']  # 工单id
        msg = post_data['msg']  # 回复的消息
    except KeyError:
        return {"code": 500, "msg": "参数有误"}
    else:
        return workorder_class.chat_send_msg(username, workorder_id, msg)


# 新建工单
@user_work_bp.route('/Workorder/Add', methods=['POST'])
@login_check
def workorder_add():
    UserName = session.get('username')  # 用户名
    form = WorkorderAdd(request.form)  # 表单验证
    if form.validate():
        _post = request.form.to_dict()  # 表单字典
        try:
            WorkorderContent = _post['WorkorderContent']  # 工单内容
            UserId = _post.get('Workorder_UserId')  # 阳光跑UserId
            AdminUser = user_class.get_admin_userlib(UserName).get("Name")  # 上级用户
        except KeyError:
            return {"code": 400, "msg": "参数有误"}
        else:
            add_msg = workorder_class.workorder_add(
                {
                    "User": UserName,
                    "UserId": UserId,
                    "AdminUser": AdminUser,
                    "WorkorderContent": WorkorderContent,
                }
            )
            return jsonify(add_msg)
    else:
        errors = {field.name:  field.errors for field in form if form.errors}
        return jsonify({"code": 400, "errors": errors})


# 关闭工单
@user_work_bp.route('/Workorder/Close', methods=['POST'])
@login_check
def workorder_close():
    username = session.get('username')
    """获取post参数"""
    post_data = request.form.to_dict()
    """获取参数"""
    try:
        workorder_id = post_data['workorder_id']  # 工单ID
    except KeyError:
        return {"code": 400, "msg": "参数有误"}
    else:
        return workorder_class.close(username, workorder_id)


        
