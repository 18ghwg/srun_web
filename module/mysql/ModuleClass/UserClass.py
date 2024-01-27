# -*- coding: utf-8 -*-
"""
@Time    : 2022/12/9 16:15
@Author  : ghwg
@File    : UserClass.py
用户操作类
"""
from datetime import datetime, timedelta
from typing import Union

from flask import url_for
from sqlalchemy import func

from config import logger
from exts import db, app
from module.mysql.ModuleClass.EmailClass import email_class
from module.mysql.ModuleClass.WebClass import web_class
from module.mysql.models import Users, IMEICodes, ResetPassword, NRunIMEICodes, VipUsers, Kamis, Agent, SystemLog, \
    Workorder
from module.mysql.modus import search_sql_info, get_sql_list, global_search_info


# 用户操作类


class UserClass:
    # 用户注册
    @classmethod
    def user_register(cls, **info) -> dict:
        # 开始注册用户信息
        add_data = Users(UserName=info['username'], Password=info['password'], Email=info['email'], QQh=info['qqh'])
        db.session.add(add_data)
        db.session.commit()  # 提交信息
        email_class.del_register_info(info['email'])  # 删除验证信息
        return {"code": 200, "msg": "用户注册成功"}

    # 用户登录校验
    @classmethod
    def check_user_login(cls, username: str, password: str) -> bool:
        _data = Users.query.filter(Users.UserName == func.binary(username),
                                   Users.Password == func.binary(password)).first()
        if _data:  # 账号密码正确
            return True
        else:
            return False

    # 获取用户密码
    @classmethod
    def get_user_password(cls, UserName: str) -> Union[str, None]:
        """
        :param UserName: 用户名
        :return: None或者用户密码
        """
        """搜索数据库信息"""
        _sql = Users.query.filter_by(UserName=UserName).first()
        if _sql:  # 搜到用户了
            """获取用户信息"""
            Password = _sql.Password
            return Password
        else:
            return None

    # 获取用户身份
    @classmethod
    def get_user_lib(cls, UserName: str):
        """
        :param UserName: 用户名
        :return: 用户身份或None
        """
        """搜索用户"""
        user_data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if user_data:
            return user_data.UserLib
        else:
            return None

    # 通过QQ互联openid获取用户名和密码
    @classmethod
    def use_openid_get_username_and_password(cls, openid: str) -> Union[None, dict]:
        """
        :param openid: QQ互联用户登录的唯一标识
        :return: None：用户没用绑定该openid； dict：用户账号密码username,password
        """
        # 通过openid搜索用户
        search_data = Users.query.filter_by(OpenId=openid).first()
        if search_data:  # 搜到了
            # 获取用户信息
            username = search_data.UserName  # 用户名
            password = search_data.Password  # 密码
            return {"username": username, "password": password}
        else:  # 没查到绑定openid的用户
            return None

    # 代理后台统计账号信息
    @classmethod
    def user_get_index_info(cls, UserName: str) -> dict:
        """
        :param UserName: 代理账号
        :return: InValidNum: 有效的数量；ValidNum：无效的数量；IMEICodeNum：账号的数量；RunToday：今天跑步的数量。
        """

        # 获取7天内用户数据
        def get_week_data(UserLib: str):
            today = datetime.today()
            dates = []  # 一周内的日期
            AddIMEICodeNums = []  # 一周内添加的imei数量
            AddVipNums = []  # 一周内添加的vip数量
            for i in range(7):
                date = today - timedelta(days=i)
                dates.append(date.strftime("%d")+"号")

                """获取数据"""
                if UserLib == "管理员":
                    imeinum = len(IMEICodes.query.filter(func.DATE(IMEICodes.Time) == date.date()).all())
                    vipnum = len(VipUsers.query.filter(func.DATE(VipUsers.JoinDate) == date.date()).all())
                else:
                    imeinum = len(IMEICodes.query.filter(func.DATE(IMEICodes.Time) == date.date(), IMEICodes.User == UserName).all())
                    vipnum = len(VipUsers.query.filter(func.DATE(VipUsers.JoinDate) == date.date(), VipUsers.User == UserName).all())
                AddIMEICodeNums.append(imeinum)
                AddVipNums.append(vipnum)
            return {"AddIMEICodeNums": AddIMEICodeNums, "AddVipNums": AddVipNums, "Weeks": dates}

        """获取用户身份"""
        user_lib = cls.get_user_lib(UserName)
        """获取信息"""
        if user_lib == "管理员":
            IMEICodeNum = len(IMEICodes.query.filter_by().all())
            RunToday = len(IMEICodes.query.filter(
                func.DATE(IMEICodes.RunDate) == datetime.now().date()).all())  # 今天跑步的数量
            ValidNum = len(IMEICodes.query.filter_by(State=1).all())  # 有效IMEICode数量
            InValidData = IMEICodes.query.filter_by(State=0).all()  # 失效账号数据
            InValidNum = len(InValidData)  # 失效IMEICode数量
        else:
            IMEICodeNum = len(IMEICodes.query.filter(IMEICodes.User == func.binary(UserName)).all())
            RunToday = len(IMEICodes.query.filter(
                IMEICodes.User == func.binary(UserName),
                func.DATE(IMEICodes.RunDate) == datetime.now().date()
            ).all())  # 今天跑步的数量
            ValidNum = len(IMEICodes.query.filter(IMEICodes.User == func.binary(UserName),
                                                  IMEICodes.State == 1).all())  # 有效IMEICode数量
            InValidData = IMEICodes.query.filter(IMEICodes.User == func.binary(UserName),
                                                 IMEICodes.State == 0).all()  # 失效账号数据
            InValidNum = len(InValidData)  # 失效IMEICode数量

        """统计失效人员姓名"""
        InValidName = []
        for User in InValidData:
            InValidName.append(User.Name)  # 加入到人员列表中
        InValidName = "、".join(InValidName)  # 提取列表元素用、分隔
        """统计一周内数据"""
        week_data = get_week_data(user_lib)
        WeekIMEICode = week_data.get("AddIMEICodeNums")
        WeekVip = week_data.get("AddVipNums")
        Weeks = week_data.get("Weeks")
        info = {
            "RunToday": RunToday,
            "IMEICodeNum": IMEICodeNum,
            "ValidNum": ValidNum,
            "InValidNum": InValidNum,
            "InValidName": InValidName,
            "WeekIMEICode": WeekIMEICode,
            "WeekVip": WeekVip,
            "Weeks": Weeks,
        }
        return info

    # 获取用户基本信息
    @classmethod
    def get_user_info(cls, UserName: str) -> dict:
        """
        :param UserName: 代理用户账号
        :return: 包含用户基本信息的字典；未获取到：{}
        """
        """获取数据库信息"""
        _sql = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if _sql:  # 用户存在
            """开始获取信息"""
            user_info = search_sql_info(Users, [{"attribute": 'UserName', "value": UserName}])[0]
            return user_info
        else:
            return {}

    # 用户修改信息
    @classmethod
    def put_user_info(cls, info: dict) -> dict:
        """
        :param info: 传入的用户信息字典
        :return: 修改结果字典
        """
        """获取字典信息"""
        UserName = info.get("UserName")
        Password = info.get("Password")
        QQh = info.get("QQh")
        """搜索数据"""
        _sql = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if _sql:  # 用户存在
            updata = {"QQh": QQh}
            if Password:  # 更新密码了
                updata.update({"Password": Password})
            else:  # 没更新密码
                pass
            """更新信息"""
            put_sql_info(UserName, updata)  # 更新信息
            return {"code": 200, "msg": "用户信息已更新"}
        else:
            return {"code": 400, "msg": "用户不存在"}

    # 管理员修改用户信息
    @classmethod
    def put_user_info_admin(cls, UserName: str, UserInfo: dict):
        """
        :param UserName: 用户名
        :param UserInfo: 用户信息的字典
        :return: 修改状态字典信息
        """
        """搜索用户"""
        user_data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if user_data:
            """更新用户信息"""
            user_data.Password = UserInfo["Password"]
            user_data.Email = UserInfo["Email"]
            user_data.QQh = UserInfo["QQh"]
            user_data.WxUid = UserInfo["WxUid"]
            user_data.UserLib = UserInfo["UserLib"]
            db.session.commit()  # 提交更新
            return {"code": 200, "msg": "用户信息已更新"}
        else:
            return {"code": 400, "msg": "用户不存在"}

    # 判断重置密码token是否存在
    @classmethod
    def check_repassword_token(cls, token: str) -> bool:
        """
        :param token: url中的密钥,用户重置密码的唯一标识
        :return: True：密钥存在 False：密钥不存在
        """
        """搜索数据"""
        _data = ResetPassword.query.filter(ResetPassword.Token == func.binary(token)).first()
        if _data:  # 搜到数据了 -> 密钥存在
            return True
        else:  # 未搜到密钥数据 -> 密钥不存在
            return False

    # 删除密码重置信息
    @classmethod
    def del_reset_password_info(cls, token) -> bool:
        """
        :param token: 密码验证密钥,url中有,用来区别用户
        :return: True:删除成功  False:删除失败
        """
        """搜索密码重置数据"""
        _data = ResetPassword.query.filter(ResetPassword.Token == func.binary(token)).first()
        if _data:
            ResetPassword.query.filter(ResetPassword.Token == func.binary(token)).delete(False)
            db.session.commit()  # 提交数据
            return True
        else:
            return False

    # 用户重置密码
    @classmethod
    def reser_user_password(cls, token: str, new_password: str):
        """
        :param token: 重置密码的密钥,在url中,用来区分用户
        :param new_password: 用户新设置的密码
        :return: 重置密码状态字典
        """
        """搜索重置密码数据"""
        _data = ResetPassword.query.filter(ResetPassword.Token == func.binary(token)).first()
        if _data:  # 信息存在
            """获取用户信息"""
            UserName = _data.UserName  # 用户名
            Email = _data.Email  # 邮箱
            """设置用户密码"""
            user_data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
            """删除重置信息"""
            cls.del_reset_password_info(token)
            if user_data:  # 用户存在
                user_data.Password = new_password
                """重置用户登录失败次数"""
                user_data.LoginFailNum = 0
                db.session.commit()  # 提交数据
                return {"code": 200, "msg": "您的密码已重置成功!"}
            else:
                return {"code": 2, "msg": "用户不存在哦~"}
        else:
            return {"code": 1, "msg": "用户重置密码信息验证失败!"}

    """获取用户列表"""

    @classmethod
    def get_user_list(cls, UserName: str, *KeyWord):
        """
        :param UserName: 用户名
        :param KeyWord: 搜索数据的关键词（可不填）
        :return: 用户列表字典
        """
        user_list = {"rows": []}  # 用户列表
        """获取用户身份"""
        UserLib = user_class.get_user_lib(UserName)
        """获取数据库"""
        if KeyWord[0]:  # 需要数据搜索
            _sql = global_search_info(Users, KeyWord[0])
        else:
            _sql = get_sql_list(Users, Users.Time, True)
        if _sql:  # 搜到数据了
            num = 0
            """处理数据库信息"""
            for imei in _sql:
                num += 1
                user_info = {
                    "id": num,
                    "UserName": imei["UserName"],
                    "Password": imei["Password"],
                    "Email": imei["Email"],
                    "WxUid": imei["WxUid"],
                    "QQh": imei["QQh"],
                    "UserLib": imei["UserLib"],
                    "Time": str(imei["Time"]),
                }
                user_list['rows'].append(user_info)
            user_list['total'] = len(user_list['rows'])
            return user_list
        else:
            return user_list

    # 删除用户
    @classmethod
    def del_user(cls, UserNameList: list):
        FailUserList = []  # 删除失败用户列表
        return_msg = ''  # 返回的信息
        for UserName in UserNameList:
            """搜索用户"""
            user_data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
            if user_data:
                """删除用户"""
                Users.query.filter(Users.UserName == func.binary(UserName)).delete(False)
                """删除账号下数据"""
                ResetPassword.query.filter(ResetPassword.UserName == func.binary(UserName)).delete(False)  # 删除找回密码数据
                IMEICodes.query.filter(IMEICodes.User == func.binary(UserName)).delete(False)  # 删除账号下跑步账号
                NRunIMEICodes.query.filter(NRunIMEICodes.User == func.binary(UserName)).delete(False)  # 删除账号下未跑步数据
                VipUsers.query.filter(VipUsers.User == func.binary(UserName)).delete(False)  # 删除账号下vip
                Kamis.query.filter(Kamis.UseUser == func.binary(UserName)).delete(False)  # 使用卡密
                Kamis.query.filter(Kamis.SCUser == func.binary(UserName)).delete(False)  # 生成卡密
                Agent.query.filter(Agent.AgentUser == func.binary(UserName)).delete(False)  # 代理
                db.session.commit()  # 提交信息
                logger.info(f"网站用户{UserName}在系统的所有信息已被删除")
            else:
                logger.error(f"网站用户{UserName}删除失败erro：用户不存在")
                FailUserList.append(UserName)  # 加入删除失败列表
        if FailUserList:  # 有删除失败的用户
            return {"code": 400, "msg": f"用户{'、'.join(FailUserList)}删除失败erro：用户不存在<br>其余用户均已删除成功"}
        else:
            return {"code": 200, "msg": f"网站用户{'、'.join(UserNameList)}删除成功"}

    # 获取账号登录失败次数
    @classmethod
    def get_user_login_fail_num(cls, UserName: str) -> int:
        """
        :param UserName: 用户名
        :return: （int）用户登录失败次数, 0：获取用户数据失败
        """
        """搜索用户"""
        user_data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if user_data:
            UserLoginFailNum = user_data.LoginFailNum  # 登录失败次数
            return UserLoginFailNum
        else:
            return 0

    # 登录失败次数加一
    @classmethod
    def add_user_fail_num(cls, UserName: str) -> bool:
        """
        :param UserName: 用户名
        :return: True：成功增加 False:获取用户数据失败
        """
        """获取用户数据"""
        user_data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if user_data:
            """开始增加登录失败次数"""
            user_data.LoginFailNum += 1
            db.session.commit()  # 提交数据
            logger.info(f"{UserName}登陆失败次数已加1")
            return True
        else:
            logger.info(f"{UserName}登陆失败次数添加失败，未找到该用户")
            return False

    # 上传用户openid
    @classmethod
    def up_user_openid(cls, username: str, openid: str):
        # 检查用户是否有其他用户绑定该openid
        _data = Users.query.filter(Users.OpenId == openid).first()
        if _data:  # 该openid已存在
            if _data.UserName != username:  # 被其他用户绑定过了
                return False
        put_sql_info(username, {"OpenId": openid})  # 上传openid
        return True

    # 解除用户QQ绑定
    @classmethod
    def relieve_binding(cls, username: str):
        if put_sql_info(username, {"OpenId": None}):
            return True
        else:
            return False

    # 构造返回后台消息提示
    @classmethod
    def get_user_message(cls, username: str) -> dict:
        # 获取用户信息
        user_data = Users.query.filter(Users.UserName == func.binary(username)).first()
        # 获取用户工单
        user_workorder = Workorder.query.filter(Workorder.User == func.binary(username) or Workorder.AdminUser == func.binary(username)).all()
        if user_data:
            # 构造字典格式
            msg_json = {
                "code": 200,
                "msgs": [],
            }
            # 构建消息
            _msg = {"title": "", "content": "", "url": ""}
            # 用户没有绑定QQ
            if not user_data.OpenId:
                _msg = {"title": "QQ未绑定", "content": "账号QQ未绑定点击绑定", "url": f"{url_for('user.binding_qq')}"}
                msg_json["msgs"].append(_msg)  # 插入消息
            # 用户没有绑定公众号订阅
            if not user_data.WxUid:
                _msg = {"title": "微信订阅未绑定", "content": "微信通知未绑定点击绑定", "url": f"{url_for('user.sub_wx_msg')}"}
                msg_json["msgs"].append(_msg)
            # 其他消息
            if user_workorder:  # 获取到工单数据
                num = 0  # 工单序号
                for workorder_data in user_workorder:
                    if workorder_data.CheckStatus == 0:  # 工单未查看
                        num += 1  # 序号
                    else:
                        pass

                    if workorder_data.CheckStatus == 0:  # 工单未查看 ->通知
                        _msg = {"title": f"新的工单回复[{num}]", "content": f"你有工单新回复[{num}]", "url": f"{url_for('user_work.chat')}?WorkorderID={workorder_data.id}"}
                        msg_json["msgs"].append(_msg)


            msg_json["msgnum"] = len(msg_json["msgs"])  # 消息数
            return msg_json
        else:
            return {"code": 400, "msg": "用户信息获取失败！"}


    # 用户签到获取积分
    @classmethod
    def user_check(cls, username: str):
        """
        :param username: 用户名
        :return: dict
        """
        _user = Users.query.filter(Users.UserName == func.binary(username)).first()
        if _user:
            CheckState = _user.CheckState  # 签到状态
            CheckDate = _user.CheckDate.date()  # 签到时间
            if not CheckState or (CheckDate < datetime.now().date()):  # 今天没有签到
                # 获取签到配置
                web_config = web_class.get_web_config()
                credit_num = web_config['UserCheckCreditNum']  # 签到获取的积分数
                # 加积分and修改签到状态
                _user.Credit += credit_num
                _user.CheckState = 1
                _user.CheckDate = datetime.now()
                db.session.commit()
                return {"code": 200, "msg": f"今日签到成功, 获得积分{credit_num}个, 账户余额：{_user.Credit}"}
            else:  # 今日已签到
                return {"code": 400, "msg": "签到失败erro:今日已签到"}
        else:  # 用户不存在
            return {"code": 400, "msg": "签到失败erro：用户不存在"}

    # 获取用户积分余额
    @classmethod
    def get_user_credit_num(cls, username: str):
        """
        :param username: 用户名
        :return: int 用户积分余额
        """
        user_data = Users.query.filter(Users.UserName == func.binary(username)).first()
        if user_data:
            return user_data.Credit
        else:
            return 0

    # 扣除用户积分
    @classmethod
    def reduce_credit(cls, username: str, num: int):
        """
        :param username: 用户名
        :param num: 数量
        :return: 无
        """
        user_data = Users.query.filter(Users.UserName == func.binary(username)).first()
        if user_data:
            user_data.Credit -= num
            db.session.commit()
        else:
            return

    # 获取用户签到状态
    @classmethod
    def get_user_check_state(cls, username: str):
        """
        :param username: 用户名
        :return: dict
        """
        _user = Users.query.filter(Users.UserName == func.binary(username)).first()
        if _user:
            if _user.CheckState == 0 or (_user.CheckDate.date() < datetime.now().date()):  # 今日没有签到
                return {"code": 200, "msg": "用户今日未签到", "check_state": False}
            else:
                return {"code": 200, "msg": "用户今日已签到", "check_state": True}
        else:
            return {"code": 400, "msg": "获取用户签到状态失败：用户信息获取失败"}

    # 判断用户a是否为用户b的下级
    @classmethod
    def is_subordinate(cls, User: str, AdminUser: str):
        """
        :param User: 下级用户
        :param AdminUser: 上级用户
        :return: User是AdminUser下级：True 反之False
        """
        """获取用户数据"""
        admin_data = Users.query.filter(Users.UserName == func.binary(User),
                                        Users.AdminUser == func.binary(AdminUser)).first()
        if admin_data:
            return True
        else:
            """判断是否为管理员"""
            UserLib = cls.get_user_lib(AdminUser)
            if UserLib:
                if UserLib == "管理员":
                    return True
                else:
                    return False
            else:
                return False

    # 检测用户是否存在
    @classmethod
    def check_user_existence(cls, UserName: str):
        """
        :param UserName: 用户名
        :return: 检测用户是否存在，True：存在 False：不存在
        """
        user_data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if user_data:
            return {"exists": True}
        else:
            return {"exists": False}

    # 获取上级用户身份
    @classmethod
    def get_admin_userlib(cls, UserName: str) -> Union[dict, str]:
        """
        :param UserName: 网站用户名
        :return: {"Name": AdminUserName, "Lib": UserLib}
        """
        user_data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if user_data:
            return {"Name": user_data.AdminUser, "Lib": cls.get_user_lib(user_data.AdminUser) if not None else ""}
        else:
            return ""

    # 创建用户日志
    @classmethod
    def add_user_system_log(cls, UserName: str, **LogInfo):
        """
        :param UserName: 用户名
        :param LogInfo: 日志字典信息
        :return: True：创建日志成功，False：用户名不存在
        """
        if cls.check_user_existence(UserName):  # 用户存在

            """获取字典信息"""
            LogContent = LogInfo.get("LogContent")  # 日志内容
            LogLib = LogInfo.get("LogLib")  # 日志类别
            """创建数据"""
            add_data = SystemLog(LogContent=LogContent, LogLib=LogLib, UserName=UserName)
            db.session.add(add_data)
            db.session.commit()  # 提交数据
            return True
        else:
            return False

    # 获取用户系日志
    @classmethod
    def get_user_system_log(cls, UserName: str, *KeyWord) -> dict:
        """
        :param UserName: 用户名
        :return: 用户的系统日志字典信息
        """
        print(KeyWord)
        log_list = {"rows": []}  # 用户系统日志列表
        """获取用户身份"""
        user_lib = user_class.get_user_lib(UserName)
        """获取数据库"""
        if user_lib == "管理员":
            if KeyWord[0]:  # 需要搜索数据
                _sql = global_search_info(SystemLog, KeyWord[0])
            else:
                _sql = get_sql_list(SystemLog, SystemLog.Time, True)
        else:  # 用户
            if KeyWord[0]:  # 需要搜索数据
                _sql = global_search_info(SystemLog, KeyWord[0],
                                          **{"UserName": UserName, "Key": "UserName", "UserLib": user_lib})
            else:
                _sql = search_sql_info(SystemLog, [{"attribute": 'UserName', "value": UserName, "order_by": "Time", "sort_order": "desc"}])
        if _sql:  # 搜到数据了
            num = 0
            """处理数据库信息"""
            for log in _sql:
                num += 1
                log_info = {
                    "id": num,
                    "LogContent": log["LogContent"],
                    "LogLib": log["LogLib"],
                    "UserName": log["UserName"],
                    "Time": str(log["Time"]),
                }
                log_list['rows'].append(log_info)
            log_list['total'] = len(log_list['rows'])
            return log_list
        else:
            return log_list

    # 通过用户名获取用户微信订阅id
    @classmethod
    def get_user_wxuid(cls, UserName: str) -> Union[str, None]:
        """
        :param UserName: 网站用户名
        :return: 微信订阅uid，未获取到：None
        """
        user_data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if user_data:
            return user_data.WxUid  # 返回微信订阅uid
        else:  # 用户不存在
            return None

    # 获取用户头像链接
    @classmethod
    def get_user_icon(cls, username: str):
        """获取用户信息"""
        user_info = cls.get_user_info(username)
        if user_info:
            qqh = user_info["QQh"]
        else:
            qqh = 123456
        return f'http://q2.qlogo.cn/headimg_dl?dst_uin={qqh}&spec=100'



# 修改用户信息
def put_sql_info(UserName: str, dic: dict) -> bool:
    """
    :param UserName: 用户名
    :param dic: 包含组名key和value的字典
    :return: True or False
    """

    _data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
    if _data:
        _data.update(dic)
        with app.app_context():
            db.session.commit()
        return True
    else:
        return False


# 实例化
user_class = UserClass()
