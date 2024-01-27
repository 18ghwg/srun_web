from datetime import datetime
from config import logger
from exts import db, app
from module.mysql import NRunIMEICodes, IMEICodes, VipUsers, Users


# 修改imei状态
from module.mysql.ModuleClass.UserClass import user_class


def modstate(UserName: str, IMEIInfo: dict, abled: str):
    """
    :param UserName: 网站用户名
    :param IMEIInfo: 阳光跑字典信息包括：IMEICode、UserId、Name
    :param abled: enabled：启用、disabled：禁用
    :return: str: 操作状态
    """
    """获取信息"""
    IMEICode = IMEIInfo.get("IMEICode")
    UserId = IMEIInfo.get("UserId")
    Name = IMEIInfo.get("Name")

    logger.info("尝试修改imei状态")
    able = 1  # 状态码
    if abled == "enabled":  # 启用
        able = 1
    elif abled == "disabled":  # 禁用
        able = 0
    # 修改
    with app.app_context():
        _data = IMEICodes.query.filter_by(IMEICode=IMEICode).first()
        if _data:
            _data.State = able
            db.session.commit()  # 提交数据
            search_data = IMEICodes.query.filter_by(IMEICode=IMEICode).first()
            state = search_data.State  # 读取IMEICode状态
            if state == able:
                logger.info(f"{abled}成功")
            else:
                logger.info(f"{abled}失败！")
            """记录系统日志"""
            user_class.add_user_system_log(UserName,
                                           **{
                                               "LogContent": f"姓名：{Name}UserId：{UserId}的跑步账号已被{'禁用' if able==0 else '启用'}",
                                               "LogLib": f"<span class='badge bg-{'yellow' if able==0 else 'success'}'>IMEICode{'禁用' if able==0 else '启用'}</span>"
                                           })
        else:
            logger.info("获取用户信息失败")


# 删除imei
def delimei(UserName: str, IMEIInfo: dict):
    """
    :param UserName: 网站用户名
    :param IMEIInfo: 阳光跑账号字典信息包含Name、UserId
    :return:
    """
    logger.info("尝试删除imei账号")
    """获取信息"""
    IMEICode = IMEIInfo.get("IMEICode")
    Name = IMEIInfo.get("Name")  # 姓名
    UserId = IMEIInfo.get("UserId")  # 阳光跑userid
    with app.app_context():
        imei_data = IMEICodes.query.filter_by(IMEICode=IMEICode).first()
        if imei_data:
            # 获取信息
            with app.app_context():
                IMEICodes.query.filter_by(IMEICode=IMEICode).delete()  # 删除IMEICode
                NRunIMEICodes.query.filter_by(IMEICode=IMEICode).delete()  # 在未跑步列表中一并删除
                db.session.commit()  # 提交数据
                """记录系统日志"""
                user_class.add_user_system_log(UserName,
                                               **{
                                                   "LogContent": f"姓名：{Name}UserId：{UserId}的跑步账号已被删除",
                                                   "LogLib": "<span class='badge bg-danger'>IMEICode删除提醒</span>"
                                               })
                logger.info("删除成功！")

        else:
            logger.info("账号不存在：删除失败")


# 增加跑步次数
def runnums(UserId: str):
    logger.info("尝试记录跑步次数")
    with app.app_context():
        _data = IMEICodes.query.filter_by(UserId=UserId).first()
        _data.RunNum += 1  # 添加跑步次数
        db.session.commit()  # 提交数据
        logger.info("跑步次数获取成功！")
        return f"你在本站成功跑步：{_data.RunNum}次"


# 添加IMEICode到未跑步列表
def add_nrun_imei(info: dict):
    logger.info("尝试添加imei到未跑步列表")
    IMEICode = info.get('IMEICode')
    UserId = info.get('UserId')
    Name = info.get('Name')
    Email = info.get('Email')
    WxUid = info.get('WxUid')
    State = info.get('State')
    VipLib = info.get('VipLib')
    VipedDate = info.get('VipedDate')
    VipRunNum = info.get('VipRunNum')  # vip次数
    User = info.get('User')  # 代理账号
    with app.app_context():
        _data = NRunIMEICodes.query.filter_by(IMEICode=IMEICode).first()
        if _data:  # 已存在
            _data.IMEICode = IMEICode
            _data.UserId = UserId
            _data.Email = Email
            _data.WxUid = WxUid
            _data.VipLib = VipLib
            _data.VIpedDate = VipedDate
            _data.VipRunNum = VipRunNum
            _data.User = User
        else:
            add_data = NRunIMEICodes(IMEICode=IMEICode, Email=Email, Name=Name, State=State,
                                     VipLib=VipLib, VipedDate=VipedDate, VipRunNum=VipRunNum,
                                     WxUid=WxUid, User=User, UserId=UserId)
            db.session.add(add_data)
        db.session.commit()  # 提交
        logger.info(f"UserId：{UserId}已加入未跑步列表！")


# 在未跑步列表中删除IMEICode
def del_nrun_imei(IMEICode: str):
    logger.info("尝试删除未跑步imei")
    with app.app_context():
        _data = NRunIMEICodes.query.filter_by(IMEICode=IMEICode).first()
        if _data:  # 搜到
            NRunIMEICodes.query.filter_by(IMEICode=IMEICode).delete()
            db.session.commit()  # 提交
            logger.info(f"{_data.Name}已从未跑步列表中删除！")
        else:
            pass


# 减少vip次数
def reduce_vip_num(userid):
    logger.info("尝试减少跑步次数")
    vip_data = VipUsers.query.filter_by(UserId=userid).first()
    user_data = IMEICodes.query.filter_by(UserId=userid).first()
    if vip_data:
        """获取用户跑步次数"""
        vip_run_num = vip_data.VipRunNum
        if vip_run_num >= 1:  # 只有you跑步次数余额才会减少次数
            user_data.VipRunNum -= 1  # 减少一次
            vip_data.VipRunNum -= 1
            db.session.commit()  # 提交数据
            logger.info(f"剩余跑步次数为：{vip_data.VipRunNum}")
            return True
        else:
            return False
    else:
        return False


# 设置最后一次跑步日期
def set_runeddate(UserId: str):
    logger.info("尝试设置最后一次跑步日期")
    with app.app_context():
        _data = IMEICodes.query.filter_by(UserId=UserId).first()
        if _data:
            """设置最后一次跑步日期"""
            _data.RunDate = datetime.now()
            db.session.commit()
            logger.info("已设置最后一次的跑步日期")
            return True
        else:
            logger.info("用户不存在,不能设置跑步日期")
            return False


# 通过imei获取网站账号
def imei_get_username(IMEICode: str):
    with app.app_context():
        _data = IMEICodes.query.filter_by(IMEICode=IMEICode).first()
        if _data:
            """开始获取用户名"""
            UserName = _data.User
            return UserName
        else:
            return None

