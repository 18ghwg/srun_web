# -*- coding: utf-8 -*-
"""
@Time    : 2022/12/22 16:36
@Author  : ghwg
@File    : Run.py

"""
import hashlib
import json
import random
import re
import time
from datetime import date, datetime
import requests
from exts import app
from module.mods import log_exceptions
from module.mysql import IMEICodes, NRunIMEICodes
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.ModuleClass.VipClass import vip_class
from module.send import send_email, send_wxmsg
from tasks.Run.module.mysql import add_nrun_imei, reduce_vip_num, del_nrun_imei, set_runeddate, imei_get_username
from .module import modstate, runnums, delimei
from config import logger


# run
usernum = 0  # 账号总数
cg_user = 0  # 跑步成功数量
sb_user = 0  # 跑步失败数量
mailnum = 0  # 邮件发送次数

# 生成随机码
alphabet = list('abcdefghijklmnopqrstuvwxyz')
random.shuffle(alphabet)
table = ''.join(alphabet)[:10]


def MD5(s):
    return hashlib.md5(s.encode()).hexdigest()


# 加密
def encrypt(s):
    result = ''
    for i in s:
        result += table[ord(i) - ord('0')]
    return result


# 日期格式转换
def timezh(ss):
    date_list = re.split('[年月日]', ss)[:-1]
    date_list_1 = ['0' + d if len(d) == 1 else d for d in date_list]
    date_format = '-'.join(date_list_1)
    return date_format


# 跑步有效记录查询
def check_valid_cj(IMEICode: str):
    """
    :param IMEICode:
    :return: True: 今天有成绩 False: 今天没有成绩
    """
    token_data = tokenhq(IMEICode)  # 获取token
    if isinstance(token_data, dict):  # IMEI有效
        srtoken = token_data['token']
        userid = str(token_data['userid'])
    else:
        logger.info("阳光跑token获取失败：IMEI已失效")
        return False
    url = f"http://client3.aipao.me/api/{srtoken}/QM_Runs/getResultsofValidByUser?UserId={userid}&pageIndex=1&pageSize=1"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"}
    res = requests.get(url=url, headers=header).json()
    RaceNums = res['RaceNums']  # 获取总跑步次数
    if RaceNums == 0 or len(res['listValue']) == 0:  # 判断有没有跑步记录
        logger.info("一条跑步记录都没有，现在跑！")
        return False
    else:
        cjtime = timezh(res['listValue'][0]['ResultDate'])  # 获取最近的一次跑步日期
        TodayDate = str(date.today())  # 获取今天的日期
        if TodayDate == cjtime:  # 判断今日有没有有效成绩
            logger.info("今日已有有效成绩!")
            return True
        else:
            logger.info("今日没有有效成绩！")
            return False


# Token获取
def tokenhq(code):
    API_ROOT = 'http://client3.aipao.me/api'  # client3 for Android
    # Login
    TokenRes = requests.get(
        API_ROOT + '/%7Btoken%7D/QM_Users/Login_AndroidSchool?IMEICode=' + code, headers={"version": "2.40"})
    TokenJson = json.loads(TokenRes.content.decode('utf8', 'ignore'))
    if TokenJson['Success'] == False:
        return False
    else:
        srtoken = TokenJson['Data']['Token']
        userid = TokenJson['Data']['UserId']
        return {"token": srtoken, "userid": userid}


# 检查IMEI是否有效
def check(IMEIInfo: dict, Email) -> bool:
    """
    :param IMEIInfo: 阳光跑信息字典
    :param Email: 邮箱
    :return: True：有效  False：无效
    """
    """获取信息"""
    IMEICode = IMEIInfo.get("IMEICode")
    UserId = IMEIInfo.get("UserId")
    Name = IMEIInfo.get("Name")

    token = tokenhq(IMEICode)  # IMEI获取token
    UserName = imei_get_username(IMEICode)  # 网站用户名
    if isinstance(token, dict):  # 如果IMEI有效
        check_json = requests.get('http://client3.aipao.me/api/' + token["token"] + '/QM_Users/GS',
                                  headers={'version': '2.42', 'auth': 'ABISHvbZgUKtJ/3SO1XqeFQ=='}).json()
        # print(check_json)
        if check_json['Success']:  # token有效
            logger.info(f"{IMEICode}有效，姓名:{check_json['Data']['User']['NickName']}\nUserId:{check_json['Data']['User']['UserID']}")
            return True
        else:  # 失效
            modstate(UserName, {"IMEICode": IMEICode, "UserId": UserId, "Name": Name}, 'disabled')  # 禁用账号
            nr = (
                    IMEICode + '<br>----------<br>状态失效，点按钮可重新提交！<br>' + '<td align="center"><table cellspacing="0" cellpadding="0" border="0" class="bmeButton" align="center" style="border-collapse: separate;"><tbody><tr><td style="border-radius: 5px; border-width: 0px; border-style: none; border-color: transparent; background-color: rgb(112, 97, 234); text-align: center; font-family: Arial, Helvetica, sans-serif; font-size: 18px; padding: 15px 30px; font-weight: bold; word-break: break-word;" class="bmeButtonText"><span style="font-family: Helvetica, Arial, sans-serif; font-size: 18px; color: rgb(255, 255, 255);"><a style="color: rgb(255, 255, 255); text-decoration: none;" target="_blank" draggable="false" href="http://srun.vip/" data-link-type="web" rel="noopener">👉  重新提交  👈</a></span></td></tr></tbody></table>')
            send_email(Email, nr, '阳光跑Token失效')  # 发送失效提醒邮件
            logger.info("token失效！禁用成功")
            return False
    else:  # IMEI失效
        modstate(UserName, {"IMEICode": IMEICode, "UserId": UserId, "Name": Name}, 'disabled')  # 禁用账号
        logger.info("token失效！禁用成功")
        return False


# 开始跑步
# 跑步的前提是当天没有有效成绩
# 如果符合上述条件执行跑步不在跑步时间段内
# 则判断成绩状态，无效则不发送邮件
def run(IMEICode) -> bool:
    global cg_user, sb_user, mailnum
    API_ROOT = 'http://client3.aipao.me/api'  # client3 for Android
    Version = '2.40'
    # Login
    TokenRes = requests.get(f"{API_ROOT}/%7Btoken%7D/QM_Users/Login_AndroidSchool?IMEICode={IMEICode}",
                            headers={"version": "2.40"})
    TokenJson = json.loads(TokenRes.content.decode('utf8', 'ignore'))

    if not TokenJson['Success']:  # 如果IMEI失效
        return False
    # headers
    srtoken = TokenJson['Data']['Token']
    userId = str(TokenJson['Data']['UserId'])

    timespan = str(time.time()).replace('.', '')[:13]  # 时间戳
    nonce = str(random.randint(100000, 10000000))
    sign = MD5(srtoken + nonce + timespan + userId).upper()  # sign为大写

    header = {'nonce': nonce, 'timespan': timespan,
              'sign': sign, 'version': Version, 'Accept': None, 'User-Agent': None, 'Accept-Encoding': None,
              'Connection': 'Keep-Alive'}

    # 获取用户信息
    GSurl = f"{API_ROOT}/{srtoken}/QM_Users/GS"
    GSres = requests.get(GSurl, headers=header, data={})
    GSjson = json.loads(GSres.content.decode('utf8', 'ignore'))

    Lengths = GSjson['Data']['SchoolRun']['Lengths']
    name = GSjson['Data']['User']['NickName']
    xb = GSjson['Data']['User']['Sex']

    # 开始跑步
    SRSurl = f"{API_ROOT}/{srtoken}/QM_Runs/SRS?S1=27.116333&S2=115.032906&S3={str(Lengths)}"
    SRSres = requests.get(SRSurl, headers=header, data={})
    SRSjson = json.loads(SRSres.content.decode('utf8', 'ignore'))
    # print(SRSjson)

    # 随机生成跑步数据
    if Lengths <= 1500:  # 如果路程比较少
        logger.info("路程太少，速度重构！")
        RunTime = str(random.randint(370, 420))  # 秒
    elif Lengths >= 3000:
        logger.info("路程太大，速度重构！")
        RunTime = str(random.randint(890, 970))  # 秒
    else:
        RunTime = str(random.randint(700, 800))  # 秒
    RunDist = str(Lengths + random.randint(0, 3))  # 米
    RunStep = str(random.randint(1300, 1600))  # 步数

    RunId = SRSjson['Data']['RunId']

    # 跑步结束->提交跑步记录
    EndUrl = f"{API_ROOT}/{srtoken}/QM_Runs/ES?S1={RunId}&S4={encrypt(RunTime)}&S5={encrypt(RunDist)}&S6=&S7=1&S8={table}&S9={encrypt(RunStep)}"
    EndRes = requests.get(EndUrl, headers=header)
    EndJson = json.loads(EndRes.content.decode('utf8', 'ignore'))
    # print(EndJson)

    if EndJson['Success']:
        logger.info(f"提交状态：{EndJson['Data']}")
        return True
    else:
        logger.info("[!]Fail:", EndJson['Data'])
        return False


# runall
@log_exceptions
def run_all():
    global mailnum, usernum, cg_user, sb_user
    usernum = 0
    cg_user = 0
    sb_user = 0
    with app.app_context():
        _data = IMEICodes.query.filter_by().all()  # 获取用户列表
        for user in _data:
            email_id = user.email_id
            with app.app_context():
                # 信息
                username = user.User
                email = user.Email
                wxuid = user.WxUid
                code = user.IMEICode
                userid = user.UserId
                vip_lib = user.VipLib
                viped_date = user.VipedDate
                name = user.Name
                state = user.State
                logger.info("参数获取成功：")
                logger.info("姓名：" + str(name))
            if vip_class.check_vip(userid):  # vip有效
                if state == 1:  # 如果token有效
                    if check({"IMEICode": code, "Name": name, "UserId": userid}, email):
                        usernum += 1  # 账号+1
                        if not check_valid_cj(code):  # 如果今日无有效成绩
                            if run(code):  # 跑步成功
                                runnums(userid)  # 跑步次数入库
                                logger.info(f"姓名：{name}当前跑步成绩有效，发送通知邮件！")
                                nr = f'{name}今日跑步成功<br>该成绩只有在你学校有效跑步时间段内才有效<br>修改跑步时间可到用户后台管理账号修改<br>'
                                set_runeddate(userid)  # 设置最后一次跑步日期
                                if email:  # 如果填写了邮箱
                                    send_email(email, nr, f'阳光跑成功通知{mailnum}')
                                else:
                                    send_wxmsg(nr, f"{name}跑步成功", wxuid)
                            else:
                                logger.info("跑步失败")
                            # 减少vip次数
                            if datetime.now() >= viped_date:  # 只有vip到期了才减少跑步次数
                                reduce_vip_num(userid)  # 减少次数
                        else:
                            logger.info("该账号今日已有有效成绩！")
                else:
                    logger.info("IMEICode失效！")
                    delimei(username, {"IMEICode": code, "UserId": userid, "Name": name})  # 删除token
            else:  # vip到期
                delimei(username, {"IMEICode": code, "UserId": userid, "Name": name})  # 删除token
                send_email(email, "你的账号vip已到期，请续费后重新提交Token", "阳光跑VIP到期提醒")
        logger.info("执行完成\n--------------------\n账号数量：{0}\n跑步成功：{1}\n跑步失败：{2}".format(usernum, cg_user, sb_user))


# 根据用户设置跑步时间
@log_exceptions
def run_now():
    time_now = datetime.now()  # 当前时间
    time_hour = time_now.hour  # 小时
    time_minute = time_now.minute  # 分钟
    run_time_now = f"{time_hour}:{time_minute}:00"  # 当前跑步时间
    with app.app_context():
        _data = IMEICodes.query.filter_by(RunTime=run_time_now).all()  # 按照跑步时间获取用户列表
        nrun_data = NRunIMEICodes.query.filter_by().all()  # 获取未跑步用户列表
        if nrun_data:  # 存在没有跑步的用户
            _data += nrun_data  # 把之前没跑得用户和当前时间跑步的用户列表相加
        if _data:  # 搜到用户了
            logger.info(f"【自动跑步】当前跑步时间：{run_time_now},跑步用户{len(_data)},未跑步遗留{len(nrun_data)}")
            for imei in _data:
                with app.app_context():  # 防止报错
                    User = imei.User  # 代理账号
                    Email = imei.Email  # 邮箱
                    WxUid = imei.WxUid if imei.WxUid else user_class.get_user_wxuid(User)  # 微信订阅通知：如果没有填写将使用代理用户的wxuid
                    IMEICode = imei.IMEICode  # 阳光跑IMEICode
                    UserId = imei.UserId  # 阳光体育userid
                    Name = imei.Name  # 姓名
                    VipLib = imei.VipLib  # vip类型
                    VipedDate = imei.VipedDate  # vip到期时间
                    VipRunNum = imei.VipRunNum  # vip剩余跑步次数
                    State = imei.State  # 账号状态
                    User = imei.User  # 代理的账号
                logger.info("【自动跑步】参数获取成功：")
                logger.info(f"【自动跑步】姓名：{Name}\n邮箱：{Email}")
                if datetime.now().strftime("%H:%M:%S") > \
                        datetime.strptime(f"{time_now.strftime('%H:%M:%S')[:-2]}50",
                                          "%H:%M:%S").strftime("%H:%M:%S"):  # 超时处理:  # 运行超时
                    info = {"IMEICode": IMEICode, "Name": Name, "State": State,
                            "Email": Email, "WxUid": WxUid, "VipLib": VipLib,
                            "VipedDate": VipedDate, "VipRunNum": VipRunNum,
                            "User": User, "UserId": UserId}
                    add_nrun_imei(info)  # 添加到未跑步列表
                else:
                    """删除未跑步账号"""
                    del_nrun_imei(IMEICode)
                    """校验数据"""
                    if not vip_class.check_vip(UserId):  # vip过期
                        logger.info("【自动跑步】vip到期,删除IMEICode")
                        delimei(User, {"IMEICode": IMEICode, "UserId": UserId, "Name": Name})  # 删除IMEICode
                        send_wxmsg(f"{Name}的vip已无效, 请重新续费vip<br>By:无感阳光跑", f"{Name}vip已过期",
                                   WxUid) if WxUid else send_email(Email, "你的账号vip已无效，请续费后重新提交IMEICode",
                                                                   "阳光跑VIP到期提醒") if Email else logger.error(
                            f"【自动跑步】UserId:{UserId}没有填写任何通知渠道，vip到期删除通知发送失败")
                        continue
                    if State == 0:  # IMEICode状态失效
                        logger.info("【自动跑步】IMEICode失效！")
                        delimei(User, {"IMEICode": IMEICode, "UserId": UserId, "Name": Name})  # 删除IMEICode
                        nr = f"{Name}的阳光跑账号由于失效已被自动清理"
                        send_wxmsg(nr, f"已删除{Name}的跑步账号", WxUid) if WxUid else send_email(Email, nr, f'阳光跑账号失效删除提醒') if Email else logger.error(f"【自动跑步】UserId:{UserId}未填写通知方式，删除提醒失败")
                        continue
                    if not check({"IMEICode": IMEICode, "UserId": UserId, "Name": Name}, Email):  # IMEICode失效
                        nr = f"{Name}的阳光跑账号已失效,请重新添加"
                        send_wxmsg(nr, f"{Name}的跑步账号今日失效", WxUid) if WxUid else send_email(Email, nr, f'阳光跑账号失效提醒') if Email else logger.error(f"【自动跑步】userid{UserId}没有填写通知方式，失效通知失败！")
                        continue
                    if check_valid_cj(IMEICode):  # 今天有效成绩了
                        set_runeddate(UserId)  # 设置最后跑步时间
                        logger.info(f"【自动跑步】该账号userid:{UserId}今日已有有效成绩！已自动设置最后跑步时间为当前时间")  # 这里设置跑步时间是为了不对用户补偿vip和未跑步检测到
                        continue
                    """开始执行跑步"""
                    if datetime.now() >= VipedDate:  # 只有vip次数了
                        reduce_vip_num(UserId)  # 扣除跑步次数
                    if run(IMEICode):  # 跑步成功
                        runnums(UserId)  # 跑步次数入库
                        logger.info(f"【自动跑步】姓名：{Name}当前跑步成绩有效！")
                        nr = f'{Name}今日跑步成功<br>该成绩只有在你学校有效跑步时间段内才有效' + f'<td align="center"><table cellspacing="0" cellpadding="0" border="0" class="bmeButton" align="center" style="border-collapse: separate;"><tbody><tr><td style="border-radius: 5px; border-width: 0px; border-style: none; border-color: transparent; background-color: rgb(112, 97, 234); text-align: center; font-family: Arial, Helvetica, sans-serif; font-size: 18px; padding: 15px 30px; font-weight: bold; word-break: break-word;" class="bmeButtonText"><span style="font-family: Helvetica, Arial, sans-serif; font-size: 18px; color: rgb(255, 255, 255);"><a style="color: rgb(255, 255, 255); text-decoration: none;" target="_blank" draggable="false" href="http://sportsapp.aipao.me/Manage/UserDomain_SNSP_Records.aspx/MyResutls?userId={UserId}" data-link-type="web" rel="noopener">👉  成绩查询  👈</a></span></td></tr></tbody></table>'
                        send_wxmsg(nr, f"{Name}跑步成功", WxUid) if WxUid else send_email(Email, nr, f'阳光跑成功通知{mailnum}') if Email else logger.error(f"【自动跑步】useid：{UserId}未填写通知方式，不做通知")
                        set_runeddate(UserId)  # 设置最后一次跑步日期
                    else:
                        logger.info(f"【自动跑步】UserId:{UserId}跑步失败")
            logger.info(f"执行完成\n--------------------\n耗时：{datetime.now() - time_now}")
        else:  # 当前时间没有跑步的用户
            logger.info(f"【自动跑步】当前时间{run_time_now}没有跑步的用户")


# 用户后台指定跑步
@log_exceptions
def user_run(UserName: str, UserId: str):
    """
    :param UserName: 网站用户名,用来校验用户
    :param UserId: 执行跑步的阳光跑id
    :return: 执行跑步状态字典
    """
    """获取信息"""
    _imei = IMEICodes.query.filter_by(UserId=UserId).first()
    UserType = user_class.get_user_lib(UserName)  # 用户身份
    if _imei:  # 存在
        if (_imei.User == UserName) or (UserType == "管理员"):  # 如果是用户本人操作或是管理员操作
            """信息"""
            Name = _imei.Name
            IMEICode = _imei.IMEICode
            Email = _imei.Email
            WxUid = _imei.WxUid if not _imei.WxUid and not Email else user_class.get_user_wxuid(UserName)  # 微信订阅通知：如果没有填写将使用代理用户的wxuid
            School = _imei.School
            VipLib = _imei.VipLib
            VipedDate = _imei.VipedDate
            VipRunNum = _imei.VipRunNum
            State = _imei.State
            logger.info(f"【手动跑步】\n信息获取成功：\nUserId：{UserId}\n姓名：{Name}")
            """数据校验"""
            if not check({"IMEICode": IMEICode, "UserId": UserId, "Name": Name}, Email):  # IMEICode失效
                return {"code": 3, "msg": f"{Name}的IMEICode已失效,请重新提交."}
            if not vip_class.check_vip(UserId):  # vip过期了
                return {"code": 4, "msg": f"{Name}账号vip已过期,请充值vip"}
            if check_valid_cj(IMEICode):  # 今天有成绩了
                return {"code": 5, "msg": f"{Name}账号今天已有有效成绩4"}
            """开始跑步"""
            if run(IMEICode):  # 跑步成功
                runnums(UserId)  # 跑步次数入库
                logger.info(f"姓名：{Name}当前跑步成绩有效，发送通知邮件！")
                nr = f'{Name}今日跑步成功<br>该成绩只有在你学校有效跑步时间段内才有效' + f'<td align="center"><table cellspacing="0" cellpadding="0" border="0" class="bmeButton" align="center" style="border-collapse: separate;"><tbody><tr><td style="border-radius: 5px; border-width: 0px; border-style: none; border-color: transparent; background-color: rgb(112, 97, 234); text-align: center; font-family: Arial, Helvetica, sans-serif; font-size: 18px; padding: 15px 30px; font-weight: bold; word-break: break-word;" class="bmeButtonText"><span style="font-family: Helvetica, Arial, sans-serif; font-size: 18px; color: rgb(255, 255, 255);"><a style="color: rgb(255, 255, 255); text-decoration: none;" target="_blank" draggable="false" href="http://sportsapp.aipao.me/Manage/UserDomain_SNSP_Records.aspx/MyResutls?userId={UserId}" data-link-type="web" rel="noopener">👉  成绩查询  👈</a></span></td></tr></tbody></table>'
                set_runeddate(UserId)  # 设置最后一次跑步日期
                send_wxmsg(nr, f"{Name}跑步成功", WxUid) if WxUid else send_email(Email, nr, f'阳光跑成功通知{mailnum}') if Email else logger.error(f"【手动跑步】UserId:{UserId}没有提供任何通知方式，不对其通知")
            else:
                logger.info(f"{Name}跑步失败")
                return {"code": 6, "msg": "跑步失败"}
            if datetime.now() >= VipedDate:  # 仅当vip过期时才会减少VipRunNum
                reduce_vip_num(UserId)  # 减少vip跑步次数
            return {"code": 200, "msg": f"{Name}账号跑步成功!"}
        else:
            return {"code": 2, "msg": f"你无权操作UserID:{UserId}的账号!"}
    else:
        return {"code": 1, "msg": f"阳光跑账号UserId:{UserId}不存在,检查账号是否提交!"}
