# -*- coding: utf-8 -*-
"""
@Time    : 2023/3/1 10:21
@Author  : ghwg
@File    : CheckTodayNRunUsers.py
检查今天没有跑步的用户并对用户的vip天数进行补偿
"""
from datetime import datetime, timedelta

from config import logger
from exts import app, db
from module.mods import log_exceptions
from module.mysql import IMEICodes, VipUsers, Users
from module.mysql.ModuleClass.WebClass import web_class
from module.send import send_wxmsg, send_email


# 开始检查用户
@log_exceptions
def check_today_nrun_imei():
    logger.info("【今日未跑步用户检测】开始")
    """变量定义"""
    BCUseNum = 0  # 补偿的用户数量
    UserInfos = ''  # 补偿的人员信息 姓名：Userid
    with app.app_context():
        """获取IMEICode列表"""
        imei_data = IMEICodes.query.filter_by().all()
        if imei_data:
            for imei in imei_data:
                """获取IMEICode信息"""
                with app.app_context():
                    IMEICode = imei.IMEICode
                    Name = imei.Name
                    UserId = imei.UserId
                    RunTime = imei.RunTime  # 跑步日期
                    RunDate = imei.RunDate  # 最后一次跑步的日期
                    AddDate = imei.Time  # 添加IMEICode的时间
                    Email = imei.Email  # 邮箱
                    WxUid = imei.WxUid  # 微信订阅通知
                    State = imei.State  # 账号状态
                """获取IMEICodevip信息"""
                vip_data = VipUsers.query.filter_by(UserId=UserId).first()
                if vip_data:
                    """获取vip信息"""
                    with app.app_context():
                        VipedDate = vip_data.VipedDate  # vip过期时间
                        VipRunNum = vip_data.VipRunNum  # vip跑步次数
                    """开始判断今日是否跑步并补偿vip"""
                    """
                    几种未跑步情况不对其进行补偿vip：
                    1.当天新增的IMEICode（最后一次跑步时间是None）
                    2.当天更新的IMEICode，并且当前的时间已经超过设置的跑步时间了
                    3.今天已经跑步了
                    4.用户设置的跑步时间已经超过了有效成绩规定的时间（比如说22:00）
                    5.当天IMEICode失效了
                    """
                    """获取当前时间"""
                    time_now = datetime.now()
                    year = time_now.year
                    month = time_now.month
                    day = time_now.day
                    # 异常情况1
                    if RunDate is None:
                        logger.error(f"【今日未跑步用户检测】：UserId：{UserId}为今天新增的账号，不进行vip补偿")
                    # 异常情况2
                    elif (AddDate.date() == time_now.date()) and \
                            (time_now > datetime.strptime(f'{year}-{month}-{day} {RunTime}', "%Y-%m-%d %H:%M:%S")):
                        logger.error(f"【今日未跑步用户检测】：UserId：{UserId}为今天更新的账号并且当前已经超过跑步时间了，不进行vip补偿")
                    # 异常情况3
                    elif RunDate.date() == time_now.date():
                        logger.error(f"【今日未跑步用户检测】：UserId：{UserId}用户今日已跑步，不对其进行vip补偿")
                    # 异常情况4
                    elif (datetime.strptime(f'{year}-{month}-{day} {RunTime}', "%Y-%m-%d %H:%M:%S") >=
                          datetime.strptime(f'{year}-{month}-{day} 22:00:00', "%Y-%m-%d %H:%M:%S")):
                        logger.error(f"【今日未跑步用户检测】：UserId：{UserId}用户的跑步时间太离谱，不对其进行vip补偿")
                    # 异常情况5
                    elif State == 0:
                        logger.error(f"【今日未跑步用户检测】：UserId：{UserId}用户的已失效，不对其进行跑vip补偿")
                    else:
                        BCUseNum += 1
                        UserInfos += f"姓名：{Name}：UserId：{UserId}<br>"
                        logger.info(f"【今日未跑步用户检测】：UserId：{UserId}开始补偿VIP")
                        """开始补偿vip"""
                        """获取网站配置"""
                        web_config = web_class.get_web_config()
                        BCVipedDay = web_config["BCVipedDay"]  # 补偿的VIP天数
                        BCVipRunNum = web_config["BCVipRunNum"]  # 补偿的VIP跑步次数
                        """VIP分类补偿"""
                        if VipedDate > time_now:  # 非次数VIP补偿
                            vip_data.VipedDate += timedelta(days=BCVipedDay)  # 补偿2天
                            imei.VipedDate += timedelta(days=BCVipedDay)  # 补偿2天
                            db.session.commit()  # 提交数据
                            nr = f"由于你的阳光跑账号UserId:{UserId}今日没有自动运行跑步<br>本程序已自动为您的账号补偿了{BCVipedDay}天的VIP"
                            logger.info(f"【今日未跑步用户检测】：UserId：{UserId}以对用户vip天数补偿：{BCVipedDay}天")
                        else:  # 次数VIP
                            vip_data.VipRunNum += BCVipRunNum  # 补偿2次
                            imei.VipRunNum += BCVipRunNum  # 补偿2次
                            db.session.commit()  # 提交数据
                            logger.info(f"【今日未跑步用户检测】：UserId：{UserId}以对用户vip跑步次数补偿：{BCVipRunNum}次")
                            nr = f"由于你的阳光跑账号今日没有自动运行跑步，本程序已自动为您的账号增加了{BCVipRunNum}次vip跑步次数"

                        logger.info("【今日未跑步用户检测】开始通知")
                        """发送通知"""
                        if WxUid:  # 优先微信订阅通知
                            send_wxmsg(nr, "Vip补偿提醒", WxUid)
                        elif Email:
                            send_email(Email, nr, "Vip补偿提醒")
                        else:
                            logger.error("【今日未跑步用户检测】未填写任何通知方式")
                else:
                    logger.error(f"【今日未跑步用户检测】：UserId：{UserId}不在vipusers表中")
                    continue
            """推送向管理员推送补偿结果"""
            if BCUseNum != 0:
                """获取管理员微信订阅id"""
                AdminWxUid = Users.query.filter_by(UserLib="管理员").first().WxUid
                send_wxmsg(f"今日未跑步vip已补偿{BCUseNum}个<br>补偿人员信息：<br>{UserInfos}<br>{datetime.now().date()}", f"未跑步账号vip补偿{BCUseNum}个", AdminWxUid)
            else:
                logger.error("【今日未跑步用户检测】今天没有补偿vip的用户，不进行推送")
        else:
            logger.error("【今日未跑步用户检测】；系统当前没有任何IMEICode账号")
            pass
