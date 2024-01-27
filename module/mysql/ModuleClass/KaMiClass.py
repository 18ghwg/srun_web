# -*- coding: utf-8 -*-
"""
@Time    : 2022/11/5 22:43
@Author  : ghwg
@File    : KaMiClass.py

"""
import random
from datetime import datetime

from config import logger
from exts import db
from module.mysql.ModuleClass.AgentClass import agent_class
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.models import Kamis
from module.mysql.modus import search_sql_info, get_sql_list, global_search_info
from module.srun_token import token_get_info, get_imei_info


class KaMiClass:
    """生成卡密"""

    @classmethod
    def sc_kamis(cls, num: int, KamiInfo: dict):
        """
        :param num: 生成卡密的数量
        :param KamiInfo: 包含KamiLib卡密类型、Num次数、Day会员天数的字典
        :return: 卡密内容
        """
        base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
        kami = ''
        for a in range(num):
            length = len(base_str) - 1
            random_str = ''
            for i in range(32):
                random_str += base_str[random.randint(0, length)]
            random_str = 'Srun' + random_str
            kami += random_str + '\n'  # 卡密内容
            """上传卡密"""
            add_data = Kamis(Kami=random_str, KamiLib=KamiInfo["KamiLib"], Day=KamiInfo["Day"],
                             Num=KamiInfo["Num"], SCUser=KamiInfo["SCUser"])
            db.session.add(add_data)
            db.session.commit()  # 提交
        return kami

    """导出未使用卡密"""

    @classmethod
    def export_nuse_kami(cls, lib):
        _data = Kamis.query.filter(Kamis.state == 0, Kamis.lib == lib).all()
        if _data:
            kamis = ''
            for kami in _data:
                kamis += kami.kami + '\n'
            with open('kamis.txt', 'w', encoding='utf-8') as file:
                file.write(kamis)
                file.close()  # 关闭
            return
        else:
            return None

    """获取卡密信息"""

    @classmethod
    def get_kami_info(cls, Kami: str):
        """
        :param Kami: 卡密
        :return: None：卡密不存在 dict 卡密信息/使用该卡密用户的信息
        """
        kami_data = Kamis.query.filter_by(Kami=Kami).first()
        if kami_data:  # 卡密存在
            if not kami_data.State:  # 卡密未被使用
                """开始获取卡密信息"""
                info = {
                    "Day": kami_data.Day,
                    "Num": kami_data.Num,
                    "KamiLib": kami_data.KamiLib,
                }
            else:  # 卡密已被使用->返回使用该卡密的用户信息
                info = {
                    "UseUser": kami_data.UseUser,
                    "UseDate": kami_data.UseDate,
                }
            return info
        else:  # 卡密不存在
            return None

    # 使用卡密
    @classmethod
    def use_kami(cls, info: dict):
        """
        :param info: 包含卡密信息的字典：用户名、卡密、使用者的姓名
        :return:
        """
        """获取卡密信息"""
        Kami = info.get('Kami')
        UserName = info.get('UserName')
        UseName = info.get('UseName')
        UseUserId = info.get('UseUserId')

        """搜索卡密"""
        kami_data = Kamis.query.filter_by(Kami=Kami).first()
        if kami_data:  # 卡密存在
            kami_data.UseUser = UserName  # 使用者
            kami_data.UseName = UseName  # 使用卡密的阳光跑姓名
            kami_data.UseUserId = UseUserId  # 使用卡密的阳光跑userid
            kami_data.UseDate = datetime.now()  # 使用时间
            kami_data.State = 1  # 卡密状态
            db.session.commit()  # 提交数据
            logger.info(f"卡密使用成功,信息：UserId：{UseUserId}")
            user_class.add_user_system_log(UserName,
                                           **{"LogContent": f"卡密{Kami}已被用户{UserName}使用，绑定者为姓名{UseName}UserId{UseUserId}",
                                              "LogLib": f"<span class='badge bg-cyan'>卡密使用提醒</span>"}
                                           )
            return True
        else:  # 卡密不存在
            return False

    # 用户已使用卡密列表
    @classmethod
    def get_user_use_kami_list(cls, UserName: str, *KeyWord):
        """
        :param UserName: 用户名
        :param KeyWord: 搜素的关键词
        :return: 已使用的卡密列字典
        """
        kami_list = {"rows": []}  # 卡密列表
        """获取用户身份"""
        user_lib = user_class.get_user_lib(UserName)
        if user_lib:
            """获取数据库"""
            if user_lib == "管理员":
                if KeyWord[0]:  # 需要搜索数据
                    _sql = global_search_info(Kamis, KeyWord[0])
                else:
                    _sql = get_sql_list(Kamis, Kamis.UseDate, True)
            else:
                if KeyWord[0]:  # 需要搜索数据
                    _sql = global_search_info(Kamis, KeyWord[0],
                                              **{"UserName": UserName, "UserLib": user_lib, "Key": "UseUser"})
                else:
                    _sql = search_sql_info(Kamis, [{"attribute": 'UseUser', "value": UserName, "order_by": "UseDate", "sort_order": "desc"}])
            if _sql:  # 搜到数据了
                num = 0
                """处理数据库信息"""
                for kami in _sql:
                    num += 1
                    kami_info = {
                        "id": num,
                        "Kami": kami["Kami"],
                        "KamiLib": kami["KamiLib"],
                        "Day": kami["Day"],
                        "Num": kami["Num"],
                        "UseUser": kami["UseUser"],
                        "UseName": kami["UseName"],
                        "UseDate": str(kami["UseDate"]),
                        "SCUser": kami["SCUser"],
                        "SCDate": str(kami["SCDate"]),
                        "State": kami["State"],
                    }
                    kami_list['rows'].append(kami_info)
                kami_list['total'] = len(kami_list['rows'])
                return kami_list
            else:
                return kami_list
        else:
            return kami_list

    # 用户获取未使用卡密列表
    @classmethod
    def get_user_nuse_kami_list(cls, UserName: str, *KeyWord) -> dict:
        """
        :param UserName: 用户名
        :param KeyWord: 要搜索的关键词（可不填）
        :return: 卡密列表字典信息
        """
        kami_list = {"rows": []}  # 卡密列表
        """获取用户身份"""
        UserLib = user_class.get_user_lib(UserName)
        """获取数据信息"""
        if KeyWord[0]:  # 需要搜索数据
            sql_info = global_search_info(Kamis, KeyWord[0],
                                          **{"UserName": UserName, "UserLib": UserLib, "Key": "SCUser"})
        else:
            sql_info = search_sql_info(Kamis, [{"attribute": 'SCUser', "value": UserName, "order_by": "SCDate", "sort_order": "desc"}])
        if sql_info:  # 获取到信息了
            """处理信息"""
            num = 0
            """处理数据库信息"""
            for kami in sql_info:
                num += 1
                kami_info = {
                    "id": num,
                    "Kami": kami["Kami"],
                    "KamiLib": kami["KamiLib"],
                    "Day": kami["Day"],
                    "Num": kami["Num"],
                    "SCUser": kami["SCUser"],
                    "SCDate": str(kami["SCDate"]),
                    "State": kami["State"],
                }
                if kami["State"] == 0:
                    kami_list['rows'].append(kami_info)
                else:  # 卡密已被使用
                    pass
            kami_list['total'] = len(kami_list['rows'])
            return kami_list
        else:  # 获取数据为空
            return kami_list

    # 积分兑换会员卡密
    @classmethod
    def credit_kami(cls, info: dict):
        """
        :param info: 包含卡密信息的字典
        :return:
        积分单价：抓包1；扫码2
        """

        UserName = info.get('UserName')  # 用户名
        KamiLib = info.get('KamiLib')  # 卡密类型
        KamiDayNum = int(info.get('KamiDayNum'))  # 生成卡密的天数
        # 获取用户积分余额
        UserCreditNum = user_class.get_user_credit_num(UserName)

        # 生成卡密
        def _sc_kami(price: int):
            """
            :param price: 兑换1天卡密需要的积分单价
            :return: 生成卡密的字典数据
            """
            # 判断用户积分余额是否足够
            if (KamiDayNum * price) <= UserCreditNum:
                # 生成1张卡密
                kamis = cls.sc_kamis(1, {"KamiLib": KamiLib, "Num": 0, "Day": KamiDayNum, "SCUser": UserName})
                user_class.reduce_credit(UserName, price*KamiDayNum)  # 扣除积分
                return {"code": 200, "msg": "卡密已生成", "kami": kamis}
            else:
                return {"code": 400, "msg": f"你的账户积分余额不足，生成卡密需要积分{KamiDayNum * price}个，"
                                            f"你还差{(KamiDayNum * price) - UserCreditNum}个！"}

        # 判断卡密类型
        if KamiLib == "抓包":
            return _sc_kami(1)  # 抓包卡密天卡单价1积分
        elif KamiLib == "扫码":
            return _sc_kami(2)  # 扫码卡密天卡单价2积分
        else:
            return {"code": 400, "msg": "会员类型有误！"}

    # 代理首页使用卡密添加vip
    @classmethod
    def agent_use_kami(cls, info: dict):
        """
        :param info: 包含webkey、卡密、阳光跑token的字典
        :return: 返回一个字典
        """
        """获取字典"""
        WebKey = info.get("WebKey")
        Kami = info.get("Kami")
        Token = info.get("Token")
        """获取代理账号"""
        AgentUser = agent_class.key_get_web_info(WebKey)["AgentUser"]
        if AgentUser:
            """获取阳光跑用户信息"""
            user_info = get_imei_info(Token)
            if user_info:
                Name = user_info["name"]
                School = user_info["school"]
                UserId = user_info["userid"]
                """添加vip"""
                info = {
                    "Kami": Kami,
                    "Name": Name,
                    "School": School,
                    "UserId": UserId,
                }
                from module.mysql.ModuleClass.VipClass import vip_class
                vip_data = vip_class.add_vip(AgentUser, info)  # 兑换vip
                return vip_data
            else:
                return {"code": 400, "msg": "你的IMEICode无效，请重新获取"}
        else:
            return {"code": 400, "msg": "你的上级代理不存在，请联系你的代理处理"}

    # 用户转移卡密
    @classmethod
    def kami_transfer(cls, SendUser: str, KamiList: list):
        msg = ''  # 卡密转移的信息
        kami_num = len(KamiList)  # 卡密的数量
        success_num = 0  # 转移成功数量
        for kami in KamiList:
            """获取卡密信息"""
            Kami = kami['Kami']  # 卡密
            ReceiveUser = kami['SCUser']  # 接收的用户
            UserLib = user_class.get_user_lib(SendUser)  # 发送者身份
            """检测接受者是否存在"""
            if user_class.check_user_existence(ReceiveUser):
                """判断接收卡密的用户是不是发送者下级"""
                if user_class.is_subordinate(ReceiveUser, SendUser):
                    """判断卡密是否归用户所有"""
                    if UserLib != "管理员":
                        search_data = Kamis.query.filter_by(Kami=Kami, SCUser=SendUser).first()
                    else:
                        search_data = Kamis.query.filter_by(Kami=Kami).first()
                    if search_data:
                        """开始转移"""
                        if search_data.State == 0 or UserLib == "管理员":  # 卡密未被使用或者是管理员在操作
                            search_data.SCUser = ReceiveUser
                            db.session.commit()
                            msg += f"<a style='color: green'>转移成功：卡密{Kami}</a><br>"
                            success_num += 1
                        else:  # 已被使用
                            msg += f"<a style='color: red'>转移失败：卡密{Kami}已被使用</a><br>"
                    else:
                        msg += f"<a style='color: red'>转移失败：卡密{Kami}不存在</a><br>"
                else:  # 用户不是上下级关系
                    msg += f"<a style='color:red'>转移失败：卡密{Kami}你输入的用户名{ReceiveUser}不是你的下级关系</a><br>"
            else:
                msg += f"<a style='color:red'>转移失败：接收卡密用户：{ReceiveUser}不存在</a><br>"
        return {"code": 200, "msg": msg+f"<br>共{kami_num}张卡密，转移成功{success_num}张"}


kami_class = KaMiClass()
