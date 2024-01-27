# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/27 17:12
@Author  : ghwg
@File    : WorkorderClass.py
工单系统
"""
import ast
import time

from sqlalchemy import func

from exts import db
from module.mysql import Workorder
from module.mysql.ModuleClass.IMEICodeClass import imei_class
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.modus import global_search_info, get_sql_list, search_sql_info
from module.send import send_wxmsg, send_email


class WorkorderClass:
    # 获取工单列表
    @classmethod
    def get_workorder_list(cls, UserName: str, *KeyWord):
        """
        :param UserName: 用户名
        :param KeyWord: 需要搜索的关键词(可不写)
        :return: 账号下work列表字典数据
        """
        """获取用户身份"""
        user_lib = user_class.get_user_lib(UserName)
        """获取数据库"""
        if user_lib == "管理员":
            if KeyWord[0]:  # 需要数据搜索
                _sql = global_search_info(Workorder, KeyWord[0])
            else:
                _sql = get_sql_list(Workorder, Workorder.Time, True)
        else:
            if KeyWord[0]:  # 需要数据搜索
                _sql = global_search_info(Workorder, KeyWord[0],
                                          **{"UserName": UserName, "UserLib": user_lib, "Key": "User"})
            else:
                _sql = search_sql_info(Workorder, [
                    {"attribute": 'User', "value": UserName, "order_by": "Time", "sort_order": "desc"}])
        work_list = {"rows": []}  # 构造workorder列表json
        if _sql:  # 搜到数据了
            # num = 0
            """处理数据库信息"""
            for work in _sql:
                # num += 1
                work_info = {
                    "id": work["id"],
                    "User": work["User"],
                    "UserId": work["UserId"],
                    "AdminUser": work["AdminUser"],
                    "WorkorderContent": work["WorkorderContent"],
                    "MsgList": ast.literal_eval(work["MsgList"]),
                    "State": work["State"],
                    "Time": str(work["Time"]),
                }
                work_list['rows'].append(work_info)
            work_list['total'] = len(work_list['rows'])
            return work_list
        else:
            return work_list

    # # 获取未查看工单或未回复工单
    # @classmethod
    # def get_unviewed_workorders(cls, AdminUser: str):
    #     """
    #     :param AdminUser: 工单所有者账号
    #     :return:
    #     """



    # 新建工单
    @classmethod
    def workorder_add(cls, Info: dict):
        """
        :param Info:新建工单的字典{"User": "提交工单用户", "UserId": "阳光跑UserId", "WorkorderContent": "工单内容", "AdminUser": "上级账号}
        :return: 工单提交字典状态
        """
        add_data = Workorder(User=Info['User'], AdminUser=Info['AdminUser'],
                             UserId=Info['UserId'],
                             WorkorderContent = Info['WorkorderContent'],
                             MsgList = str([{"content": {"msg": Info["WorkorderContent"], "time": time.time(), "user": Info['User']}, "notes": []}]))
        db.session.add(add_data)
        db.session.commit()
        """开始发送通知"""
        return_msg = []  # 返回信息
        AdminUserInfo = user_class.get_user_info(Info["AdminUser"])  # 上级用户信息
        UserInfo = user_class.get_user_info(Info["User"])  # 用户信息
        ygp_info = ''
        if AdminUserInfo:
            AdminEmail = AdminUserInfo.get('Email')  # 上级邮箱
            AdminWxUid = AdminUserInfo.get('WxUid')  # 上级用户微信订阅Uid
        else:
            return {"code": 400, "msg": "未获取到管理员信息"}
        if UserInfo:
            UserEmail = UserInfo["Email"]  # 用户邮箱
            UserWxUid = UserInfo["WxUid"]  # 用户微信Uid
        else:
            return {"code": 400, "msg": "未获取到用户信息"}

        if Info.get("UserId"):

            UserIdList = Info.get("UserId").split(",")  # 阳光跑UserId列表
            for UserId in UserIdList:
                IMEIInfo = imei_class.get_imei_info(Info["User"], UserId)  # 阳光跑信息
                if IMEIInfo:
                    Name = IMEIInfo["Name"]  # 姓名
                    School = IMEIInfo["School"]  # 学校
                    RunTime = IMEIInfo["RunTime"] # 跑步时间
                    IMEICode = IMEIInfo["IMEICode"] # IMEICode
                    ygp_info += f'姓名：{Name}<br>学校：{School}<br>跑步时间：{RunTime}<br>IMEICode：{IMEICode}<br>UserId：{UserId}<br>'
                else:
                    return_msg.append({"code": 400, "msg": f"未获取到UserId：{UserId}信息"})

        else:
            pass
        if AdminWxUid:
            send_wxmsg(f'【无感阳光跑】<br>你有一个新的工单:<br>'
                       f'{Info["User"]}说：{Info["WorkorderContent"]}<br>'
                       f'{"-"*20}<br>用户邮箱：{UserEmail}<br>{("-"*10+"相关阳光跑账号"+"-"*10 + ygp_info) if bool(ygp_info) else ""}',
                       f'{Info["User"]}说：{Info["WorkorderContent"][10:]}', AdminWxUid)
        else:
            send_email(AdminEmail,
                       f'【无感阳光跑】<br>你有一个新的工单:<br>{Info["User"]}说：{Info["WorkorderContent"]}<br>{"-"*20}<br>用户邮箱：{UserEmail}',
                       "新工单提醒")
        return {"code": 200, "data": "success" if bool(return_msg) is False else return_msg}

    # 修改工单状态
    @classmethod
    def put_status(cls, workorder_id: int, status: int):
        """
        :param workorder_id: 工单ID
        :param status: 工单状态码
        :return: True修改成功，False修改失败
        """
        search_data = Workorder.query.filter_by(id=workorder_id).first()
        if search_data:
            search_data.State = status
            db.session.commit()
            return True
        else:
            return False

    # 关闭工单
    @classmethod
    def close(cls, admin_user: str, workorder_id: int):
        """
        :param admin_user: 管理员账号
        :param workorder_id: 工单ID
        :return:code:200：工单关闭成功，code:500：关闭失败工单不存
        """
        """获取管理员身份"""
        user_lib = user_class.get_user_lib(admin_user)
        """搜索数据"""
        if user_lib == "管理员":
            search_data = Workorder.query.filter_by(id=workorder_id).first()
        else:
            search_data = Workorder.query.filtey(Workorder.AdminUser == func.binary(admin_user), Workorder.id == workorder_id).first()
        if search_data:
            """修改工单状态"""
            if cls.put_status(workorder_id, 2):
                return {"code": 200, "msg": "工单已关闭"}
            else:
                return {"code": 500, "msg": "error：工单关闭失败，工单不存在！"}
        else:
            return {"code": 500, "msg": "erro:工单关闭失败，工单不存在!"}

    # 获取工单回复数据
    @classmethod
    def get_msg_data(cls, username: str, workorder_id: int):
        """
        :param username: 访问工单的用户账号
        :param workorder_id: 工单所属的id
        :return:
        """
        """获取工单数据"""
        user_lib = user_class.get_user_lib(username)  # 用户身份
        if user_lib == "管理员":
            search_data = Workorder.query.filter_by(id=workorder_id).first()
        else:
            search_data = Workorder.query.filter(Workorder.User == func.binary(username), Workorder.id == workorder_id).first()
            if not search_data:
                search_data = Workorder.query.filter(Workorder.AdminUser == func.binary(username), workorder_id == workorder_id).first()

        if search_data:
            # [{"content": {"msg": Info["WorkorderContent"], "time": time.time(), "user": ""}, "notes": [{"msg": "", "time": 124324324234, "user": ""}]}]
            # [{"content": ""}, {"notes": ""}, {"notes": ""}]  # 按消息发送时间进行列表排序
            """设置工单状态为已读"""
            search_data.CheckStatus = 1
            db.session.commit()  # 提交数据从
            msg_data = []  # 消息列表
            for workorder in ast.literal_eval(search_data.MsgList):
                """获取工单数据"""
                content = workorder['content']['msg']  # 工单内容
                content_time = workorder['content']['time']  # 发送工单的时间
                content_user = workorder['content']['user']  # 创建工单的用户
                content_icon = user_class.get_user_icon(content_user)
                msg_data.append({"content": content, "time": content_time, "user": content_user, "icon": content_icon})  # 插入工单数据
                """获取回复数据"""
                if bool(workorder.get('notes')):  # 有回复数据
                    for botes_data in workorder['notes']:
                        notes = botes_data['msg']  # 回复内容
                        notes_time = botes_data['time']  # 回复时间
                        notes_user = botes_data['user']  # 回复工单的用户
                        notes_icon = user_class.get_user_icon(notes_user)
                        msg_data.append({'notes': notes, "time": notes_time, "user": notes_user, "icon": notes_icon})  # 插入回复数据

            return {"code": 200, "data": msg_data, "msg": "工单回复数据获取成功"}
        else:
            return {"code": 500, "data": [], "msg": "未获取到该工单回复数据"}

    # 回复工单
    @classmethod
    def chat_send_msg(cls, username: str, workorder_id: int, msg: str):
        """
        :param username: 回复工单的用户
        :param workorder_id: 工单ID
        :param msg: 回复内容
        :return: code: 200 成功， 400 工单不存在， 500 非法请求
        """
        """"获取用户信息"""
        user_info = user_class.get_user_info(username)
        if user_info:
            user_lib = user_info['UserLib']  # 用户类型
        else:
            return {"code": 500, "msg": "非法用户请求"}
        """获取工单数据"""
        search_data = Workorder.query.filter_by(id=workorder_id).first()
        if search_data:
            content_user = search_data.User  # 创建工单用户
            admin_user = search_data.AdminUser  # 工单所属代理用户
            workorder_content = search_data.WorkorderContent  # 工单内容
            msg_lsit: list = ast.literal_eval(search_data.MsgList)  # 获取聊天数据
            if content_user == username:  # 工单追问
                msg_lsit.append({"content": {"msg": msg, "time": time.time(), "user": username}, "notes": []})
            elif admin_user == username or user_lib == "管理员":  # 工单所属代理用户或者管理员回复工单
                 msg_lsit[-1]['notes'].append({"msg": msg, "time": time.time(), "user": username})  # 更新回复工单列表
            else:
                return {"code": 500, "msg": "非法用户请求，请停止！"}
            """保存工单数据"""
            search_data.MsgList = str(msg_lsit)
            db.session.commit()
            """"发送通知"""
            nr = f"工单：【{workorder_content}】<br>有新的回复：<br>回复内容：{msg}"
            UserInfo = user_class.get_user_info(username)  # 用户信息
            UserWxUid = UserInfo.get("WxUid")  # 微信订阅Uid
            UserEmail = UserInfo.get("Email")  # 用户邮箱

            if UserWxUid:
                send_wxmsg(nr, "工单新回复", UserWxUid)
            else:
                send_email(UserEmail, nr, "工单回复")
            return {"code": 200, "msg": "工单回复成功！"}
        else:
            return {"code": 400, "msg": "该工单不存在"}



workorder_class = WorkorderClass()


