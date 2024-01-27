# -*- coding: utf-8 -*-
"""
@Time    : 2023/2/24 9:17
@Author  : ghwg
@File    : AgentClass.py

"""
from flask import url_for
from sqlalchemy import func

from config import logger
from exts import db
from module.mysql import Agent, Users, IMEICodes, VipUsers
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.modus import search_sql_info, global_search_info
from module.send import send_email


class AgentClass:
    # 根据代理网站Key获取网站信息
    @classmethod
    def key_get_web_info(cls, WebKey: str) -> dict:
        """搜索数据"""
        agent_info = search_sql_info(Agent, [{"attribute": "WebKey", "value": WebKey}])
        if agent_info:  # 搜到数据
            return agent_info[0]
        else:
            return {}

    # 网站后台用户获取代理网站信息
    @classmethod
    def get_web_info(cls, username: str):
        """
        :param username: 网站代理用户名
        :return: 代理网站的配置
        """
        agent_info = search_sql_info(Agent, [{"attribute": 'AgentUser', "value": username}])
        if agent_info:  # 搜到数据
            return agent_info[0]
        else:
            return {}

    # 设置代理网站信息
    @classmethod
    def set_web_info(cls, UserName: str, info: dict):
        """
        :param UserName: 网站代理用户名
        :param info: 需要修改的字典
        :return: 修改结果：字典
        """
        """获取字典信息"""
        WebName = info.get('WebName')
        WebKey = info.get("WebKey")
        Kfqq = info.get("Kfqq")
        WebGG = info.get("WebGG")
        QQGroup = info.get("QQGroup")
        """代理二级域名前缀格式判断"""
        if WebKey in ['www', 'admin', 'wwww', 'main']:
            return {"code": 400, "msg": "代理域名前缀不符合规范"}
        """搜索代理"""
        agent = Agent.query.filter(Agent.AgentUser == func.binary(UserName)).first()
        if agent:  # 代理存在 -> 更新
            """判断WebKey是否重复"""
            _key = Agent.query.filter(Agent.WebKey == func.binary(WebKey), Agent.AgentUser != UserName).first()
            if not _key:  # 没有其他代理使用这个密钥
                """开始更新信息"""
                agent.WebName = WebName
                agent.WebKey = WebKey
                agent.Kfqq = Kfqq
                agent.WebGG = WebGG
                agent.QQGroup = QQGroup
                db.session.commit()  # 提交数据
                logger.info("代理网站信息已修改成功")
                return {"code": 200, "msg": "代理网站信息已修改成功"}
            else:
                logger.error("你填写的网站密钥与别人的重复哦")
                return {"code": 400, "msg": "你填写的网站密钥与别人的重复哦"}
        else:  # 代理不存在 -> 新增
            """新建代理网站"""
            add_data = Agent(AgentUser=UserName, WebName=WebName,
                             WebKey=WebKey, Kfqq=Kfqq, WebGG=WebGG,
                             QQGroup=QQGroup)
            db.session.add(add_data)
            db.session.commit()  # 提交新增数据
            logger.info("代理网站已成功新增,欢迎加入！")
            return {"code": 200, "msg": "代理网站已成功新增,欢迎加入！"}

    # 获取代理额度
    @classmethod
    def get_agent_quota(cls, AgentUserName: str):
        """
        :param AgentUserName: 代理用户名
        :return: 代理额度，未搜索到代理时返回0
        """
        """获取用户数据"""
        UserLib = user_class.get_user_lib(AgentUserName)
        if UserLib == "管理员":
            return 99
        else:
            agent_data = Users.query.filter(Users.UserName == func.binary(AgentUserName), Users.UserLib == "代理").first()
            if agent_data:
                logger.info(f"代理额度获取成功：{agent_data.AgentQuota}")
                return agent_data.AgentQuota
            else:
                return 0

    # 操作代理额度
    @classmethod
    def put_agent_quota(cls, mod: str, AgentUserName: str, Num: int):
        """
        :param mod: 操作方法 add增加；reducu减少
        :param AgentUserName: 代理用户名
        :param Num: 操作代理额度的数量
        :return: True操作成功，False操作失败
        """
        UserLib = user_class.get_user_lib(AgentUserName)
        if UserLib == "管理员":  # 管理员直接返回True
            return True
        """获取用户数据"""
        agent_data = Users.query.filter(Users.UserName == func.binary(AgentUserName), Users.UserLib == "代理").first()
        if agent_data:
            AgentQuota = agent_data.AgentQuota  # 代理额度
            if mod == "add":  # 增加
                agent_data.AgentQuota += Num
                db.session.commit()  # 提交数据
                logger.info(f"开始为用户：{AgentUserName}增加代理额度")
                return
            elif mod == "reduce":  # 减少
                logger.info(f"开始为用户：{AgentUserName}减少代理额度")
                if (AgentQuota - Num) >= 0:
                    agent_data.AgentQuota -= Num
                    db.session.commit()  # 提交数据
                    logger.info("代理额度扣除成功！")
                    return True
                else:
                    logger.error(f"操作代理额度失败，代理：{AgentUserName}的余额不足以扣除！")
                    return False
            else:
                logger.error(f"操作代理额度失败，方法：{mod}不存在")
                return False
        else:
            logger.error(f"操作代理额度失败，用户：{AgentUserName}不存在")
            return False

    # 添加代理
    @classmethod
    def add_agent(cls, info: dict):
        """
        :param info: 包含UserName、PassWord、QQh、Email的字典信息
        :return: 添加结果字典信息{"code": 0, "msg": ""}
        """
        """获取字典信息"""
        UserName = info.get("UserName")
        Password = info.get("Password")
        QQh = info.get("QQh")
        Email = info.get("Email")
        AdminUser = info.get("AdminUser")
        """获取并判断代理额度"""
        AgentQuota = cls.get_agent_quota(AdminUser)
        if AgentQuota >= 1:  # 额度足够
            """扣除代理额度"""
            if cls.put_agent_quota('reduce', AdminUser, 1):
                add_data = Users(UserName=UserName,
                                 Password=Password,
                                 QQh=QQh,
                                 Email=Email,
                                 AdminUser=AdminUser,
                                 UserLib="代理")
                db.session.add(add_data)
                db.session.commit()  # 提交账号
                """发送通知"""
                email_nr = f"代理账号开通成功<br>你的代理账号信息:<br>账号：{UserName}<br>密码：{Password}<br>邮箱：{Email}"
                send_email(Email, email_nr, "代理开通提醒")
                return {"code": 200, "msg": f"代理账号{UserName}已成功创建"}
            else:
                return {"code": 400, "msg": f"代理开通失败Error：代理额度扣除失败，请联系管理员！"}
        else:  # 代理额度不足
            return {"code": 400, "msg": f"你的账号：{AdminUser}代理额度不足，开通失败！"}

    # 获取代理用户列表
    @classmethod
    def get_agent_list(cls, UserName: str, *KeyWord):
        """
        :param UserName: 网站用户名
        :param KeyWord: 搜索数据的关键词(可不填)
        :return: 代理用户字典列表
        """
        agent_list = {"rows": []}  # 用户列表
        """获取数据库"""
        """获取用户身份"""
        UserLib = user_class.get_user_lib(UserName)
        if UserLib == "管理员":
            if KeyWord[0]:  # 需要数据搜索
                _sql = global_search_info(Users, KeyWord[0])
            else:
                _sql = search_sql_info(Users, [
                    {"attribute": "UserLib", "value": "代理", "order_by": "Time", "sort_order": "desc"}])
        elif UserLib == "代理":
            if KeyWord[0]:  # 需要搜索数据
                _sql = global_search_info(Users, KeyWord[0],
                                          **{"UserName": UserName, "UserLib": UserLib, "Key": "AdminUser"})
            else:
                _sql = search_sql_info(Users, [
                    {"attribute": "UserLib", "value": "代理", "order_by": "Time", "sort_order": "desc"},
                    {"attribute": "AdminUser", "value": UserName, "order_by": "Time", "sort_order": "desc"}])
        else:
            return {"code": 400, "msg": "不是代理用户，无权操作"}
        if _sql:  # 搜到数据了
            num = 0
            """处理数据库信息"""
            for agent in _sql:
                num += 1
                """获取代理名下账号数据"""
                IMEICodeNums = len(
                    IMEICodes.query.filter(IMEICodes.User == func.binary(agent['UserName'])).all())  # 跑步账号数量
                VipUserNums = len(
                    VipUsers.query.filter(VipUsers.User == func.binary(agent['UserName'])).all())  # vip账号数量
                """获取代理网站信息"""
                AgentWebInfo = cls.get_web_info(agent['UserName'])  # 代理网站信息
                AgentWebUrl = url_for('agent.web_index', subdomain=AgentWebInfo['WebKey'])  # 代理网站url
                user_info = {
                    "id": num,
                    "UserName": agent["UserName"],
                    "Password": agent["Password"] if UserLib == "管理员" else None,
                    "Email": agent["Email"],
                    "QQh": agent["QQh"],
                    "AgentQuota": agent["AgentQuota"],
                    "Time": str(agent["Time"]),
                    "IMEICodeNums": IMEICodeNums,
                    "VipUserNums": VipUserNums,
                    "WebUrl": AgentWebUrl,
                }
                agent_list['rows'].append(user_info)
            agent_list['total'] = len(agent_list['rows'])
            return agent_list
        else:
            return agent_list

    # 获取代理用户基本信息
    @classmethod
    def get_agent_info(cls, UserName: str, AdminUser: str) -> dict:
        """
        :param UserName: 代理用户账号
        :param AdminUser: 代理上级用户名
        :return: 包含用户基本信息的字典
        """
        """获取数据库信息"""
        _sql = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if _sql:  # 用户存在
            """开始获取信息"""
            """获取用户类型"""
            UserLib = user_class.get_user_lib(AdminUser)
            if UserLib == "代理":  # 限制只能获取自己账号下的代理账号
                info = [{"attribute": 'UserName', "value": UserName},
                        {"attribute": 'UserLib', "value": "代理"},
                        {"attribute": 'AdminUser', "value": AdminUser}]
            elif UserLib == "管理员":
                info = [{"attribute": 'UserName', "value": UserName},
                        {"attribute": 'UserLib', "value": "代理"}]
            else:  # 不是代理或者管理员用户
                return {}
            user_info = search_sql_info(Users, info)
            if user_info:
                return user_info[0]
            else:
                return {}
        else:
            return {}

    # 代理修改二级代理信息
    @classmethod
    def put_agent_info_agent(cls, UserName: str, UserInfo: dict, AdminUser: str):
        """
        :param UserName: 用户名
        :param UserInfo: 用户信息的字典
        :param AdminUser: 代理上级用户
        :return: 修改状态字典信息
        """
        """获取用户类型"""
        UserLib = user_class.get_user_lib(AdminUser)
        """搜索用户"""
        if UserLib == "管理员":
            user_data = Users.query.filter(Users.UserName == func.binary(UserName), Users.UserLib == "代理").first()
        else:
            user_data = Users.query.filter(Users.UserName == func.binary(UserName),
                                           Users.UserLib == "代理",
                                           Users.AdminUser == AdminUser).first()
        if user_data:
            """更新用户信息"""
            user_data.Email = UserInfo["Email"]
            user_data.QQh = UserInfo["QQh"]
            user_data.WxUid = UserInfo["WxUid"]
            if UserLib == "管理员":  # 如果是管理员修改的信息
                user_data.AgentQuota = UserInfo["AgentQuota"]
                user_data.Password = UserInfo["Password"]
            db.session.commit()  # 提交更新
            return {"code": 200, "msg": "代理用户信息已更新"}
        else:
            return {"code": 400, "msg": "代理用户不存在"}


# 实例化
agent_class = AgentClass()
