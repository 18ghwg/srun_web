# -*- coding: utf-8 -*-
"""
@Time    : 2023/3/1 9:11
@Author  : ghwg
@File    : SendTodayRunInfo.py
推送每日的跑步情况给账号管理员
"""
import wrapt

from config import logger
from exts import app
from module.mods import log_exceptions
from module.mysql import Users
from module.mysql.ModuleClass.UserClass import user_class
from module.send import send_wxmsg, send_email


# 推送消息主程序
@log_exceptions
def send_run_info():
    logger.info("【每日跑步情况推送】开始")
    # 获取用户列表
    with app.app_context():
        user_data = Users.query.filter(Users.UserLib != "普通用户").all()
        if user_data:
            for user in user_data:
                """获取用户信息"""
                with app.app_context():
                    UserLib = user.UserLib  # 用户类型
                    UserName = user.UserName  # 用户名
                    Email = user.Email  # 邮箱
                    WxUid = user.WxUid  # 微信订阅Uid
                """判断用户身份：管理员和代理才会推送，普通用户不会推送"""
                if UserLib == "管理员" or UserLib == "代理":
                    """获取用户账号下跑步的信息"""
                    today_data = user_class.user_get_index_info(UserName)  # 今天跑步的信息
                    """处理信息"""
                    RunToday = today_data["RunToday"]  # 今天跑步的数量
                    InValidNum = today_data["InValidNum"]  # 无效的数量
                    InValidName = today_data["InValidName"]  # 失效人员名字
                    ValidNum = today_data["ValidNum"]  # 有效账号的数量
                    IMEICodeNum = today_data["IMEICodeNum"]  # 账号下跑步账号总数
                    """构造消息内容"""
                    msg_content = f'尊敬的{UserLib}：{UserName}你好, 以下是你账号的今日跑步情况：<br>' \
                                  f'今天跑步：{RunToday}<br>' \
                                  f'有效账号：{ValidNum}<br>' \
                                  f'失效账号：{InValidNum}<br>' \
                                  f'账号总数：{IMEICodeNum}<br>' \
                                  f'失效人员：{InValidName}'
                    """开始通知"""
                    if IMEICodeNum >=1:
                        if WxUid:  # 默认用微信公众号通知
                            logger.info(f"【每日跑步情况推送】用户：{UserName}发送微信订阅通知")
                            send_wxmsg(msg_content, "今日账号跑步情况统计", WxUid)
                        elif Email:  # 邮箱推送
                            logger.info(f"【每日跑步情况推送】用户：{UserName}发送邮箱通知")
                            send_email(Email, msg_content, "今日账号跑步情况统计")
                        else:  # 没有填写通知方式
                            logger.error(f"【每日跑步情况推送】用户：{UserName}没有填写任何通知方式")
                            pass
                    else:
                        logger.info(f"【每日跑步情况推送】{UserName}账号下没有跑步账号，不进行通知")
                        pass
        else:
            logger.erro("【每日跑步情况推送】网站当前没有用户注册")
        logger.info("【每日跑步情况推送】结束")

