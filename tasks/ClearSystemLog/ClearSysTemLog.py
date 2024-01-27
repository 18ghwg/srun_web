# -*- coding: utf-8 -*-
"""
@Time    : 2023/4/5 9:34
@Author  : ghwg
@File    : ClearSysTemLog.py
清理系统日志数据库
"""
from sqlalchemy import func

from config import logger
from exts import db, app
from module.mods import log_exceptions
from module.mysql import SystemLog, Users

@log_exceptions
def clear_system_log():
    """获取用户数据"""
    with app.app_context():
        user_all = Users.query.filter_by().all()
        if len(user_all) > 0:
            for user_data in user_all:
                """获取用户信息"""
                UserName = user_data.UserName  # 用户名
                """开始获取用户日志"""
                # 最新的300条数据
                with app.app_context():
                    latest_logs = SystemLog.query.filter(SystemLog.UserName == func.binary(UserName)).order_by(SystemLog.Time.desc()).limit(300).all()
                    if len(latest_logs) > 300:
                        # 旧数据
                        with app.app_context():
                            old_logs = SystemLog.query.filter(SystemLog.id.notin_([log.id for log in latest_logs])).all()
                            """开始删除旧数据"""
                            for old in old_logs:
                                db.session.delete(old)
                            db.session.commit()  # 提交数据
                            logger.info(f"【清理用户日志】用户：{UserName}的系统日志已清理完成")
                    else:
                        pass
                        # logger.error(f"【清理用户日志】用户：{UserName}在系统中留存的日志没有超过限制，不做清理")
        else:
            logger.error(f"【清理用户日志】未获取到系统用户数据，请检查数据库中是否有用户注册！")


