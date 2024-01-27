# -*- coding: utf-8 -*-
"""
@Time    : 2022/11/5 22:15
@Author  : ghwg
@File    : IMEICodeClass.py

"""
from datetime import datetime

from config import logger
from exts import db
from module.mysql import IMEICodes, VipUsers, Users
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.ModuleClass.VipClass import vip_class
from module.mysql.ModuleClass.WebClass import web_class
from module.mysql.ModuleClass.WxPusherClass import wxpusher_class
from module.mysql.modus import get_sql_list, search_sql_info, global_search_info
from module.srun_token import get_imei_info


class IMEICodeClass:
    """用户添加IMEICode"""

    @classmethod
    def user_add_imei(cls, info: dict):
        """
        :param info: 字典信息
        :return:
        200: 添加/更新成功
        201：IMEICode无效
        202：Vip无效
        203：IMEICode已存在无需更新
        204：绑定在其他用户名下了
        205：网站用户不存在
        """
        """获取字典信息"""
        IMEICode = info.get('IMEICode')  # IMEICode
        User = info.get('User')  # 用户名
        Email = info.get('Email')  # 邮箱
        RunTime = info.get('RunTime')  # 跑步时间
        """获取IMEICode信息"""
        CodeInfo = get_imei_info(IMEICode)
        if CodeInfo is False:  # IMEICode无效
            return {"code": 201, "msg": "您给的IMEICode是无效的,请重新获取."}
        else:  # IMEICode有效
            UserId = CodeInfo.get('userid')  # 阳光体育userid
            School = CodeInfo.get('school')  # 学校
            Name = CodeInfo.get('name')  # 姓名
            """判断用户vip是否有效"""
            check_vip = vip_class.check_vip(UserId)
            if check_vip is False:  # vip无效
                return {"code": 202, "msg": "你的账号vip无效,请先去后台充值vip再提交：账号-vip充值.",
                        "kami_url": web_class.get_web_config()['KamiPayUrl']}
            """判断用户是否存在"""
            if not Users.query.filter_by(UserName=User).first():
                return {"code": 205, "msg": "用户名不存在,未注册请先注册"}
            else:  # vip有效->添加账号
                """获取vip信息"""
                vip_data = VipUsers.query.filter_by(UserId=UserId).first()
                VipLib = vip_data.VipLib  # vip类型
                VipedDate = vip_data.VipedDate  # vip过期时间
                VipRunNum = vip_data.VipRunNum  # vip剩余跑步次数
                if not vip_data.User:  # vip用户账号没有填写
                    vip_data.User = User
                else:
                    pass
                """获取wxpusherUid"""
                WxUid = wxpusher_class.userid_get_wxpusheruid(UserId)  # 微信订阅用户id
                """查询用户"""
                UserData = IMEICodes.query.filter_by(UserId=UserId).first()
                if UserData:  # 用户已存在
                    if UserData.User != User:  # 如果是不同代理添加
                        return {"code": 204, "msg": "该账号已在其他账户绑定,请等待阳光跑账号过期后重试"}
                    else:
                        if not UserData.State:  # IMEICode失效了->更新信息
                            UserData.VipLib = VipLib
                            UserData.VipedDate = VipedDate
                            UserData.VipRunNum = VipRunNum
                            UserData.Email = Email
                            UserData.WxUid = WxUid
                            UserData.IMEICode = IMEICode
                            UserData.RunTime = RunTime
                            UserData.User = User
                            UserData.State = 1
                            UserData.Time = datetime.now()  # 更新加入的时间
                            db.session.commit()
                            return {"code": 200, "msg": "IMEICode已更新,系统将会在你设置的跑步时间为你增加跑步成绩.", "userid": UserId}
                        else:  # IMEICode未失效
                            return {"code": 203, "msg": "IMEICode未失效,无需更新.", "userid": UserId}
                else:  # 不存在->新增
                    add_data = IMEICodes(IMEICode=IMEICode, RunTime=RunTime,
                                         UserId=UserId, User=User, Name=Name,
                                         School=School, Email=Email, WxUid=WxUid,
                                         VipLib=VipLib, VipedDate=VipedDate, VipRunNum=VipRunNum)
                    db.session.add(add_data)
                    db.session.commit()
                    return {"code": 200, "msg": "已成功添加IMEICode,系统将会在你设置的跑步时间为你增加跑步成绩.", "userid": UserId}

    """获取IMEICode列表"""
    @classmethod
    def get_imei_list(cls, UserName: str, *KeyWord):
        """
        :param UserName: 用户名
        :param KeyWord: 搜索的关键词（可不填）
        :return:
        """
        imei_list = {"rows": []}  # imei列表
        """获取用户身份"""
        user_lib = user_class.get_user_lib(UserName)
        """获取数据库"""
        if user_lib == "管理员":
            if KeyWord[0]:  # 需要搜索数据
                _sql = global_search_info(IMEICodes, KeyWord[0])
            else:
                _sql = get_sql_list(IMEICodes, IMEICodes.Time, True)
        else:  # 用户
            if KeyWord[0]:  # 需要搜索数据
                _sql = global_search_info(IMEICodes, KeyWord[0],
                                          **{"UserName": UserName, "Key": "User", "UserLib": user_lib})
            else:
                _sql = search_sql_info(IMEICodes, [{"attribute": 'User', "value": UserName, "order_by": "Time", "sort_order": "desc"}])
        if _sql:  # 搜到数据了
            num = 0
            """处理数据库信息"""
            for imei in _sql:
                num += 1
                imei_info = {
                    "id": num,
                    "Name": imei["Name"],
                    "School": imei["School"],
                    "UserId": imei["UserId"],
                    "RunTime": str(imei["RunTime"]),
                    "VipedDate": str(imei["VipedDate"]),
                    "VipRunNum": imei["VipRunNum"],
                    "VipLib": imei["VipLib"],
                    "RunDate": str(imei["RunDate"]),
                    "State": imei["State"],
                    "User": imei["User"],
                    "Time": str(imei["Time"]),
                }
                imei_list['rows'].append(imei_info)
            imei_list['total'] = len(imei_list['rows'])
            return imei_list
        else:
            return imei_list

    """返回跑步账号信息"""
    @classmethod
    def get_imei_info(cls, UserName: str, UserId: int):
        """
        :param UserName: 代理账号
        :param UserId: 阳光跑用户userid
        :return: 跑步用户字典信息, 正常返回用户字典信息, 未搜到返回空字典
        代理用户名用来判断是不是本人在操作
        """
        """获取用户身份"""
        user_lib = user_class.get_user_lib(UserName)
        """搜索数据库数据"""
        if user_lib != "管理员":
            sql_data = IMEICodes.query.filter_by(User=UserName, UserId=UserId).first()
        else:
            sql_data = IMEICodes.query.filter_by(UserId=UserId).first()
        if sql_data:  # 搜到数据了
            """获取数据信息"""
            info = {
                "User": sql_data.User,
                "IMEICode": sql_data.IMEICode,
                "Name": sql_data.Name,
                "School": sql_data.School,
                "UserId": sql_data.UserId,
                "RunTime": sql_data.RunTime,
                "State": sql_data.State,
                "Email": sql_data.Email if sql_data.Email else '',
            }
            return info
        else:
            return {}

    """代理用户修改跑步信息"""
    @classmethod
    def set_imei_info(cls, UserName: str, UserInfo: dict):
        """
        :param UserName: 代理账号
        :param UserInfo: 被修改跑步用户的信息
        :return: 修改结果字典
        """
        """获取用户信息"""
        IMEICode = UserInfo.get("IMEICode")
        UserId = UserInfo.get("UserId")
        Email = UserInfo.get("Email")
        RunTime = UserInfo.get("RunTime")
        User = UserInfo.get("User")
        State = int(UserInfo.get("State"))
        """数据格式判断"""
        if State != 0 and State != 1:
            return {"code": 400, "msg": "参数有误."}
        """获取用户身份"""
        user_lib = user_class.get_user_lib(UserName)
        """搜索数据库信息"""
        if user_lib != "管理员":
            sql_data = IMEICodes.query.filter_by(User=UserName, UserId=UserId).first()
        else:
            sql_data = IMEICodes.query.filter_by(UserId=UserId).first()
        if sql_data:  # 用户存在
            """修改用户信息"""
            if User:  # 如果更改了用户名
                sql_data.User = User
            sql_data.IMEICode = IMEICode
            sql_data.Email = Email
            sql_data.RunTime = RunTime
            sql_data.State = State
            sql_data.Time = datetime.now()  # 更新IMEICode加入的时间
            """提交数据信息"""
            db.session.commit()
            return {"code": 200, "msg": "用户跑步信息修改成功"}
        else:  # 用户不存在,或者不属于请求的代理
            return {"code": 400, "msg": "该跑步账号不存在"}

    # 代理删除IMEICode
    @classmethod
    def del_imei(cls, UserName: str, UserIdList: list):
        """
        :param UserName: 代理账号
        :param UserIdList: 阳光跑用户id删除的列表
        :return: 删除结果字典信息
        """
        """获取用户身份"""
        user_lib = user_class.get_user_lib(UserName)
        """搜索数据库信息"""
        NameList = []  # 已删除姓名列表
        FailList = []  # 删除失败姓名列表
        for UserId in UserIdList:
            if user_lib != "管理员":
                _sql = IMEICodes.query.filter_by(User=UserName, UserId=UserId).first()
            else:
                _sql = IMEICodes.query.filter_by(UserId=UserId).first()
            if _sql:  # 用户存在
                """日志"""
                logger.info(f"{_sql.Name}UserId:{UserId}的跑步账号已被账号管理员删除")
                NameList.append(_sql.Name)  # 姓名加入删除列表
                """删除操作"""
                IMEICodes.query.filter_by(UserId=UserId).delete()
                db.session.commit()  # 提交
            else:  # 用户不存在或没权操作
                logger.info(f"UserId:{UserId}的跑步账号删除失败：账号不存在")
                FailList.append(UserId)
        """返回信息"""
        if NameList:  # 如果没有删除失败的
            return {"code": 200, "msg": f"{'、'.join(NameList)}的阳光跑账号已成功删除"}
        else:  # 有删除失败的
            if FailList and NameList:  # 删除成功和删除失败的都有
                return {"code": 400, "msg": f"{'、'.join(FailList)}删除失败，账号不存在<br>"
                                            f"{'、'.join(NameList)}的跑步账号删除成功"}
            else:  # 只有删除失败的
                return {"code": 400, "msg": f"{'、'.join(FailList)}的阳光跑账号删除失败，账号不存在"}

    # 代理首页更新跑步时间
    @classmethod
    def put_imei_runtime(cls, IMEICode: str, RunTime: str) -> dict:
        if not get_imei_info(IMEICode):
            return {"code": 400, "msg": "IMEICode无效"}
        else:
            """开始更新跑步时间"""
            imei_data = IMEICodes.query.filter_by(IMEICode=IMEICode).first()
            if imei_data:
                imei_data.RunTime = RunTime
                db.session.commit()  # 提交数据
                return {"code": 200, "msg": f"IMEICode的跑步时间已更新为:{RunTime}"}
            else:
                return {"code": 400, "msg": "系统中未找到你的IMEICode"}


# 实例化
imei_class = IMEICodeClass()
