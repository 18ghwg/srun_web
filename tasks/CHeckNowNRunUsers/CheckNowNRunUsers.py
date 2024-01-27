# -*- coding: utf-8 -*-
"""
@Time    : 2023/3/4 9:55
@Author  : ghwg
@File    : CheckNowNRunUsers.py
当前检测几分钟前没有跑步的用户，并加入到未跑步列表中
"""
from datetime import datetime, timedelta, time
from exts import app, db
from sqlalchemy import func

from config import logger
from module.mods import log_exceptions
from module.mysql import IMEICodes
from tasks.Run.module.mysql import add_nrun_imei


@log_exceptions
def check_now_nrun_imei():
    check_minute = 5  # 获取几分钟前的数据
    """获取当前时间"""
    now_time = datetime.now() - timedelta(minutes=check_minute)  # 获取前check_minute分钟前的数据
    hour = now_time.hour  # 时
    minute = now_time.minute  # 分
    logger.info(f"【检测当前未跑步用户】开始, 当前时间{datetime.now().hour}:{datetime.now().minute},检测跑步时间{hour}:{minute}")
    """获取5分钟前未跑步账号数据"""
    """
    1.不对今天添加的账号检测
    2.不对无效账号检测
    3.不对今天跑步的用户检测
    4.不对vip已经到期的用户检测
    """
    with app.app_context():
        nrun_data = IMEICodes.query.filter(IMEICodes.RunTime == f"{hour}:{minute}",
                                           func.DATE(IMEICodes.Time) != now_time.date(),
                                           IMEICodes.State == 1,
                                           func.DATE(IMEICodes.RunDate) != now_time.date(),
                                           IMEICodes.VipedDate >= now_time).all()
        if nrun_data:
            for imei in nrun_data:
                logger.info("【检测当前未跑步用户】开始获取用户信息")
                """获取用户信息"""
                with app.app_context():
                    IMEICode = imei.IMEICode
                    Name = imei.Name
                    UserId = imei.UserId
                    Email = imei.Email
                    WxUid = imei.WxUid
                    State = imei.State
                    VipLib = imei.VipLib
                    VipedDate = imei.VipedDate
                    VipRunNum = imei.VipRunNum
                    User = imei.User
                    logger.info(f"【检测当前未跑步用户】UserId:{UserId}，姓名：{Name}")
                """构建字典"""
                info = {
                    "IMEICode": IMEICode,
                    "UserId": UserId,
                    "Name": Name,
                    "Email": Email,
                    "WxUid": WxUid,
                    "State": State,
                    "VipLib": VipLib,
                    "VipedDate": VipedDate,
                    "VipRunNum": VipRunNum,
                    "User": User,
                }
                """加入到未跑步列表内"""
                add_nrun_imei(info)
            logger.info("【检测当前未跑步用户】检测结束")
        else:
            logger.error("【检测当前未跑步用户】未在系统中找到符合条件的用户，检测结束")
