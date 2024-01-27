# -*- coding: utf-8 -*-
"""
@Time    : 2022/11/5 22:44
@Author  : ghwg
@File    : VipClass.py

"""
from datetime import timedelta, datetime


from config import logger
from exts import db
from module.mysql import VipUsers, VipLib
from module.mysql.ModuleClass.KaMiClass import kami_class
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.modus import get_sql_list, search_sql_info, global_search_info


class VipClass:
    # 检查用户是否为vip用户
    @classmethod
    def check_vip(cls, UserId: int):
        """
        :param UserId: 阳光跑userid
        :return: True：是， False：不是
        """
        user_data = VipUsers.query.filter_by(UserId=UserId).first()
        if user_data:
            """到期时间和跑步次数判断"""
            if (datetime.now() <= user_data.VipedDate) or (user_data.VipRunNum >= 1):  # 未到期或者还有跑步次数
                logger.info(f"UserId：{UserId}vip有效")
                return True
            else:  # 已到期或没有跑步次数
                logger.info(f"UserId：{UserId}已到期或没有跑步次数")
                return False
        else:  # 不是vip
            logger.info(f"UserId：{UserId}不是Vip用户")
            return False

    # 查询vip到期时间
    @classmethod
    def get_viped_date(cls, userid: int):
        """
        :param userid: 阳光跑userid
        :return: 不是vip：当前时间 vip：到期时间
        """
        _data = VipUsers.query.filter_by(UserId=userid).first()
        if _data:
            return _data.VipedDate
        else:
            return datetime.now()

    # 查询vip剩余跑步次数
    @classmethod
    def get_vip_run_num(cls, userid: int):
        """
        :param userid:  阳光跑userid
        :return: 不是vip：0 vip：vip跑步次数
        """
        _data = VipUsers.query.filter_by(UserId=userid).first()
        if _data:
            return _data.VipRunNum
        else:
            return 0

    # 获取vip类型
    @classmethod
    def get_vip_lib(cls, userid: int):
        """
        :param userid: 阳光跑userid
        :return: None:不是vip用户 str:vip类型
        """
        _data = VipUsers.query.filter_by(UserId=userid).first()
        if _data:
            return _data.VipLib
        else:
            return None

    # 获取vip类型列表
    @classmethod
    def get_vip_lib_list(cls):
        _sql = get_sql_list(VipLib, VipLib.id)
        return _sql

    # 添加/续费Vip
    @classmethod
    def add_vip(cls, UserName: str, info: dict):
        """
        :param UserName: 代理用户名
        :param info: 包含添加vip的信息
        :return: dic: 成功：code:200
                      失败：code：400
                      {“code”:xx, "msg": "xx"}
        """
        """获取需要的字典信息"""
        Kami = info.get('Kami')
        Name = info.get('Name')
        School = info.get('School')
        UserId = info.get('UserId')
        """获取卡密信息"""
        kami_info = kami_class.get_kami_info(Kami)
        if kami_info and kami_info.get("UseUser") is None:  # 卡密存在and卡密未被使用
            """使用卡密"""
            kami_class.use_kami({"UserName": UserName, "Kami": Kami, "UseName": Name, "UseUserId": UserId})
            """搜索vip"""
            vip_data = VipUsers.query.filter_by(UserId=UserId).first()
            if vip_data:  # vip用户->更新vip余额
                # 更新VipUsers表数据
                vip_data.User = UserName  # 更新代理账号
                VipedDate = vip_data.VipedDate  # 当前vip过期时间
                vip_data.VipLib = kami_info["KamiLib"]  # vip类型
                vip_data.VipRunNum += kami_info["Num"]  # 增加跑步次数
                # 判断Vip是否过期
                if vip_data.VipedDate > datetime.now():  # vip没有过期 -> 直接增加vip天数
                    vip_data.VipedDate = VipedDate + timedelta(days=kami_info['Day'])  # 增加到期时间
                else:  # vip已过期 -> 在充值卡密的时间上增加vip天数
                    vip_data.VipedDate = datetime.now() + timedelta(days=kami_info['Day'])
                db.session.commit()  # 提交数据
                logger.info(f"卡密使用成功，vip时长已更新UserId：{UserId}")
                return {"code": 200, "msg": f"Vip余额更新成功<br>你是用的是{kami_info['KamiLib']}卡密<br>"
                                            f"你的vip天数共增加了{kami_info['Day']}天<br>"
                                            f"跑步次数增加了{kami_info['Num']}次."}
            else:  # 普通用户->新增vip
                add_data = VipUsers(Name=Name, School=School,
                                    UserId=UserId, VipLib=kami_info["KamiLib"],
                                    VipedDate=datetime.now() + timedelta(days=kami_info["Day"]),
                                    VipRunNum=kami_info["Num"], User=UserName)
                db.session.add(add_data)
                db.session.commit()  # 提交数据
                logger.info(f"卡密使用成功，vip用户UserId:{UserId}已新增")
                return {"code": 200, "msg": f"欢迎新同学加入Vip<br>你是用的是{kami_info['KamiLib']}卡密<br>"
                                            f"本次为您vip天数增加了{kami_info['Day']}天<br>"
                                            f"跑步次数增加了{kami_info['Num']}次"}
        else:  # 卡密无效
            if kami_info is None:  # 卡密不存在
                logger.info(f"卡密{Kami}不存在")
                return {"code": 400, "msg": "你输入的卡密无效,请检查卡密是否复制完整."}
            else:  # 卡密已经被使用了
                """使用卡密用户判断"""
                if UserName == kami_info["UseUser"]:
                    logger.info(f"这张卡密：{Kami}已被你使用过了")
                    return {"code": 400, "msg": "这张卡密已被你使用过了"}
                else:  # 被其他用户使用了
                    logger.info(f"这张卡密:{Kami}已被其他用户使用了,使用卡密的用户为{kami_info['UseUser']}")
                    return {"code": 400, "msg": f"这张卡密已被其他用户使用了,使用卡密的用户为{kami_info['UseUser'][:-2]}**"}

    # 获取账号下vip列表
    @classmethod
    def get_vip_list(cls, UserName: str, *KeyWord):
        """
        :param UserName: 用户名
        :param KeyWord: 需要搜索的关键词(可不写)
        :return: 账号下vip列表字典数据
        """
        """获取用户身份"""
        user_lib = user_class.get_user_lib(UserName)
        """获取数据库"""
        if user_lib == "管理员":
            if KeyWord[0]:  # 需要数据搜索
                _sql = global_search_info(VipUsers, KeyWord[0])
            else:
                _sql = get_sql_list(VipUsers, VipUsers.JoinDate, True)
        else:
            if KeyWord[0]:  # 需要数据搜索
                _sql = global_search_info(VipUsers, KeyWord[0],
                                          **{"UserName": UserName, "UserLib": user_lib, "Key": "User"})
            else:
                _sql = search_sql_info(VipUsers, [{"attribute": 'User', "value": UserName, "order_by": "JoinDate", "sort_order": "desc"}])
        vip_list = {"rows": []}  # 构造vip列表json
        if _sql:  # 搜到数据了
            num = 0
            """处理数据库信息"""
            for vip in _sql:
                num += 1
                vip_info = {
                    "id": num,
                    "Name": vip["Name"],
                    "School": vip["School"],
                    "UserId": vip["UserId"],
                    "VipedDate": str(vip["VipedDate"]),
                    "VipRunNum": vip["VipRunNum"],
                    "VipLib": vip["VipLib"],
                    "JoinDate": str(vip["JoinDate"]),
                }
                vip_list['rows'].append(vip_info)
            vip_list['total'] = len(vip_list['rows'])
            return vip_list
        else:
            return vip_list

    # 删除用户vip
    @classmethod
    def del_vip(cls, UserName: str, UserId: int):
        """
        :param UserName: 代理账号
        :param UserId: 阳光跑用户id
        :return: 删除结果字典信息
        """
        """获取用户身份"""
        user_lib = user_class.get_user_lib(UserName)
        """搜索数据库信息"""
        if user_lib != "管理员":
            _sql = VipUsers.query.filter_by(User=UserName, UserId=UserId).first()
        else:
            _sql = VipUsers.query.filter_by(UserId=UserId).first()
        if _sql:  # 用户存在
            """删除操作"""
            if user_lib != "管理员":
                VipUsers.query.filter_by(User=UserName, UserId=UserId).delete()
            else:
                VipUsers.query.filter_by(UserId=UserId).delete()
            db.session.commit()  # 提交
            return {"code": 200, "msg": "您账号下vip已删除成功"}
        else:  # 用户不存在或没权操作
            return {"code": 400, "msg": "vip账号不存在"}

    # 获取vip字典信息
    @classmethod
    def get_vip_info(cls, UserId: str) -> dict:
        """
        :param UserId: 阳光跑用户id
        :return: vip字典信息
        """
        # 搜索vip
        search_data = search_sql_info(VipUsers, [{"attribute": 'UserId', "value": UserId}])
        if search_data:
            return search_data[0]
        else:
            return {}

    # 修改vip用户信息
    @classmethod
    def set_vip_info(cls, UserName: int, PutInfo: dict) -> dict:
        """
        :param UserName: 网站用户名
        :param PutInfo: 接收的需要修改的信息
        :return: 修改状态信息字典
        """
        # 获取字典数据
        UserId = PutInfo.get('UserId')  # 阳光跑id
        VipLib = PutInfo.get('VipLib')  # 会员类型
        VipedDate = PutInfo.get('VipedDate')  # vip到期时间
        VipRunNum = PutInfo.get('VipRunNum')  # vip剩余跑步次数
        User = PutInfo.get('User')
        # 搜索数据
        _data = VipUsers.query.filter_by(UserId=UserId).first()
        if _data:
            # 获取用户身份
            UserLib = user_class.get_user_lib(UserName)
            if (UserName != _data.User) and UserLib != "管理员":  # 被修改的vip不是当前登录的用户所有
                logger.info(f"{UserId}的vip信息不归{UserName}所有， 修改失败")
                return {"code": 400, "msg": "当前vip账号不归你所有，无权修改"}
            else:
                # 开始修改信息
                _data.VipLib = VipLib
                _data.VipedDate = VipedDate
                _data.VipRunNum = VipRunNum
                _data.User = User
                db.session.commit()  # 提交修改
                logger.info(f"{UserId}的vip信息已成功修改")
                return {"code": 200, "msg": "vip信息已修改"}
        else:
            logger.info(f"{UserId}的vip信息不存在")
            return {"code": 400, "msg": "修改失败，vip用户不存在"}



vip_class = VipClass()
