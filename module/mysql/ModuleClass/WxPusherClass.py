# -*- coding: utf-8 -*-
"""
@Time    : 2023/3/6 9:27
@Author  : ghwg
@File    : WxPusherClass.py

"""
from sqlalchemy import func

from config import logger
from exts import db
from module.mysql import WxPusher, IMEICodes, Users
from module.send import send_wxmsg


class WxPusherClass:
    # wxpusher消息回调设置uid
    @classmethod
    def wxpusher_post_set_uid(cls, post_data: dict):
        """获取信息"""
        UserId = str(post_data["data"]["content"]).replace(" ", "")  # 阳光跑id
        Uid = post_data["data"]["uid"]
        """校验数据"""
        try:
            UserId = int(UserId)
        except ValueError:
            logger.info("用户发送的内容不是阳光跑UserId")
            send_wxmsg(f"你发送的代码不是网站提供的", f"绑定失败，代码有误", Uid)
            return
        else:
            """搜索跑步信息"""
            _data = IMEICodes.query.filter_by(UserId=UserId).first()
            if _data:
                _data.WxUid = Uid
                db.session.commit()  # 提交
                logger.info(f"UserId：{UserId}的通知已设置")
                """保存用户的WxUid"""
                cls.save_userid_wxpusheruid(UserId, Uid)
                """获取姓名"""
                Name = _data.Name
                """推送订阅成功消息"""
                send_wxmsg(f"{Name}的跑步账号已成功绑定消息通知", f"{Name}的账号通知已绑定", Uid)
            else:
                send_wxmsg(f"绑定失败，未提交过账号", f"绑定失败，未提交过账号", Uid)
                logger.info(f"UserId：{UserId}不存在，没有提交过账号")

    # 通过阳光跑UserId获取获取的WxPusher的Uid
    @classmethod
    def userid_get_wxpusheruid(cls, UserId: str) -> [str, None]:
        """
        :param UserId: 阳光跑用户id
        :return: wxpusheruid or None
        """
        _data = WxPusher.query.filter_by(UserId=UserId).first()
        if _data:
            logger.info("用户wxpusheruid已存在，获取成功！")
            return _data.WxUid
        else:
            logger.info(f"UserId:{UserId}的wxpusher不存在")
            return None

    # 保存/更新阳光跑用户的wxpusheruid
    @classmethod
    def save_userid_wxpusheruid(cls, UserId: int, WxUid: str):
        """
        :param UserId: 阳光跑用户id
        :param WxUid: wxpusherUid
        :return: 无
        """
        imei_data = IMEICodes.query.filter_by(UserId=UserId).first()
        _data = WxPusher.query.filter_by(UserId=UserId).first()
        """更新IMEICode的WxUid"""
        if imei_data:
            imei_data.WxUid = WxUid
        else:
            pass
        """保存阳光跑用户的WxUid到表中"""
        if _data:
            """更新"""
            _data.WxUid = WxUid
            db.session.commit()
            logger.info(f"UserId:{UserId}的wxpusher已更新")
        else:
            """添加"""
            add_data = WxPusher(UserId=UserId, WxUid=WxUid)
            db.session.add(add_data)
            db.session.commit()  # 提交数据
            logger.info(f"UserId:{UserId}的wxpusher已新增到表中")

    # 二维码关注回调
    # 获取wx公众号订阅回调并提交订阅用户uid
    @classmethod
    def set_wx_uid(cls, res: dict):
        """处理回调信息"""
        extra_data = res["data"]["extra"]  # 订阅消息的用户名
        Uid = res["data"]["uid"]  # 订阅用户的uid
        """判断是网站用户绑定还是代理首页客户提交的userid"""
        if "username" in extra_data:  # 网站用户绑定通知
            UserName = str(extra_data).split(":")[1]  # 网站用户名
            """搜索用户数据"""
            user_sql = Users.query.filter(Users.UserName == func.binary(UserName)).first()
            if user_sql:  # 搜到数据
                """设置用户通知Uid"""
                user_sql.WxUid = Uid
                db.session.commit()  # 提交数据
                logger.info("【设置微信订阅】用户微信订阅uid已设置")
                send_wxmsg(f"用户{UserName}微信订阅已绑定", f"用户{UserName}微信订阅成功绑定", Uid)
                return True
            else:  # 没搜到用户
                logger.info("【设置微信订阅】用户未找到")
                send_wxmsg(f"用户{UserName}不存在，绑定通知失败", f"用户{UserName}不存在，绑定通知失败", Uid)
                return False
        elif "userid" in extra_data:  # 阳光跑绑定通知
            UserId = int(str(extra_data).split(":")[1])  # 阳光跑用户id
            """获取阳光跑用户信息"""
            imei_data = IMEICodes.query.filter_by(UserId=UserId).first()
            if imei_data:
                Name = imei_data.Name  # 姓名
                """更新保存阳光跑用户的wxuid"""
                cls.save_userid_wxpusheruid(UserId, Uid)
                logger.info(f"【设置微信订阅】阳光跑userid：{UserId}微信订阅uid已设置,姓名：{Name}")
                """发送推送消息"""
                send_wxmsg(f"{Name}的阳光跑微信订阅已绑定", f"{Name}的阳光跑微信订阅成功绑定", Uid)
                return True
            else:
                logger.info(f"【设置微信订阅】阳光跑userid：{UserId}微信订阅通知设置失败，为提交账号")
                """发送推送消息"""
                send_wxmsg(f"阳光跑通知绑定失败<br>原因：未提交账号，请先提交账号后操作", f"未提交IMEICode绑定失败", Uid)
                return False
        else:  # 二维码参数有误
            logger.info(f"【设置微信订阅】二维码参数有误，设置失败")
            """发送通知"""
            send_wxmsg(f"二维码参数有误请联系网站管理员", f"二维码参数有误，绑定通知失败", Uid)
            return False


# 实例化
wxpusher_class = WxPusherClass()

