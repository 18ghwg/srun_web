# coding=utf-8
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Union

import requests
import random
from config import logger
from module.mysql.ModuleClass.WebClass import web_class
from module.mysql.ModuleClass.SendClass import send_class


# 邮件发送
# 参数介绍：
# a邮箱
# b内容
def send_email(useremail: str, nr: str, subject: str):
    """
    :param useremail: 接收邮箱
    :param nr: 邮件内容
    :param subject: 邮件主题
    :return:
    """
    """获取邮箱配置"""
    EmailConfig = web_class.get_web_config()
    try:
        email_nr = f"""<div style="background-color: white; border-top: 2px solid #12ADDB; box-shadow: 0 1px 3px #AAAAAA; line-height: 180%; padding: 0 15px 12px; width: 500px; margin: 50px auto; color: #555555; font-family: 'Century Gothic', 'Trebuchet MS', 'Hiragino Sans GB', 微软雅黑, 'Microsoft Yahei', Tahoma, Helvetica, Arial, 'SimSun', sans-serif; font-size: 12px;">
    <h2 style="border-bottom: 1px solid #DDD; font-size: 14px; font-weight: normal; padding: 13px 0 10px 8px;">
        <span style="color: #12ADDB; font-weight: bold;">&gt; </span>系统消息
    </h2>
    <div style="padding: 0 12px 0 12px; margin-top: 18px;">
        <p>{nr}</p>
        <p>
            本邮件为自动发送，如有疑问，联系我
            <a style="text-decoration: none; color: #12ADDB;" href="mailto:ghwg18@qq.com" target="_blank">观后无感</a>。
        </p>
    </div>
</div>
"""
        mail_from = f'mail{random.randint(0, 200)}@blog18.cn'  # 发件人账号
        password = 'Sun0218..'  # 邮件密码
        subject = subject  # 邮件标题
        subtype = 'html'  # 邮件类型
        url = 'http://124.222.113.243:2180/mail_sys/send_mail_http.json'  # 宝塔邮局接口
        pdata = {'mail_from': mail_from, 'password': password, 'mail_to': useremail, 'subject': subject,
                 'content': email_nr,
                 'subtype': subtype}
        resp_data = requests.post(url=url, data=pdata, timeout=2).json()
        logger.info("邮件发送成功！")
        return resp_data['status']
    except Exception as e:
        logger.info(f"邮件发送失败！{e}")
        return send_email2(useremail, nr, subject)


def send_email2(useremail, nr, subject) -> bool:
    """
    :param useremail: 接收邮件的邮箱
    :param nr: 邮件内容格式为html
    :param subject: 邮件的主题
    :return: True发送成功 False发送失败
    """
    """获取邮箱配置"""
    EmailConfig = web_class.get_web_config()
    try:
        my_sender = 'lelege@admin.blog18.cn'  # 发件人邮箱账号
        my_pass = 'SUNle20020218'  # 发件人邮箱密码
        stmpurl = "smtpdm.aliyun.com"  # stmp服务器地址
        msg = MIMEText(
            f'<div style="background-color: white; border-top: 2px solid #12ADDB; box-shadow: 0 1px 3px #AAAAAA; line-height: 180%; padding: 0 15px 12px; width: 500px; margin: 50px auto; color: #555555; font-family: "Century Gothic", "Trebuchet MS", "Hiragino Sans GB", 微软雅黑, "Microsoft Yahei", Tahoma, Helvetica, Arial, "SimSun", sans-serif; font-size: 12px;">    <h2 style="border-bottom: 1px solid #DDD; font-size: 14px; font-weight: normal; padding: 13px 0 10px 8px;"><span style="color: #12ADDB; font-weight: bold;">&gt; </span>系统消息</h2><div style="padding: 0 12px 0 12px; margin-top: 18px;"><p>{nr}</p><p>本邮件为自动发送，如有疑问，联系我<a style="text-decoration: none; color: #12ADDB;" href="mailto:ghwg18@qq.com" target="_blank">观后无感</a>。        </p>    </div></div>',
            'html', 'utf-8')
        msg['From'] = formataddr(["无感阳光跑", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To'] = formataddr(["同学", useremail])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = f"{subject}"  # 邮件的主题，也可以说是标题

        server = smtplib.SMTP_SSL(stmpurl, 465)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(my_sender, [useremail, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
        logger.info("邮件发送成功！")
        return True
    except:
        logger.info("邮件发送失败！")
        return False


# 企业应用推送
# 获取token
def get_token() -> Union[str, None]:
    """获取网站配置"""
    WebConfig = web_class.get_web_config()
    CorpID = WebConfig.get("CorpID")
    CorpSecret = WebConfig.get("CorpSecret")

    token = send_class.get_access_token()
    # token检测
    check_res = requests.get(f"https://qyapi.weixin.qq.com/cgi-bin/get_api_domain_ip?access_token={token}").json()
    if check_res["errcode"] == 40014 or check_res["errcode"] == 42001:  # access_token失效
        logger.info("access_token已失效，正在重新获取...")
        _res = requests.get(
            f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CorpID}&corpsecret={CorpSecret}").json()
        try:
            token = _res["access_token"]
            send_class.put_access_token(token)
            return token
        except Exception as e:
            logger.info(f"获取token失败，原因：{e}")
            return None
    else:  # access_token有效
        logger.info("access_token有效")
        return token


# 发送企业应用消息
def sendwxbot(nr) -> bool:
    """获取网站配置"""
    WebConfig = web_class.get_web_config()
    AgentID = WebConfig.get("AgentID")

    token = get_token()
    if token is None:
        return False
    else:
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        msg = {
            "touser": "@all",
            "msgtype": "markdown",
            "agentid": AgentID,
            "markdown": {"content": nr},
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }
        res = requests.post(url=url, json=msg).json()
        if res['errcode'] == 0:
            logger.info("微信应用通知发送成功！")
            return True
        else:
            logger.info("微信应用通知发送失败！")
            return False


# 给订阅用户推送消息
def send_wxmsg(content: str, summary: str, uid: str) -> bool:
    """
    :param content: 消息内容
    :param summary: 消息摘要,显示在消息模板中
    :param uid: 接收消息的用户
    :return: True发送成功 False发送失败
    """
    """获取数据配置"""
    _cnf = web_class.get_web_config()
    appToken = _cnf['WxAppToken']  # 微信推送通讯密钥
    api_url = 'https://wxpusher.zjiecode.com/api/send/message'
    data = {
        "appToken": appToken,
        "content": f'<div style="background-color:white;border-top:2px solid #12ADDB;box-shadow:0 1px 3px #AAAAAA;line-height:180%;padding:0 15px 12px;width:380px;margin:50px auto;color:#555555;font-family:"Century Gothic","Trebuchet MS","Hiragino Sans GB",微软雅黑,"Microsoft Yahei",Tahoma,Helvetica,Arial,"SimSun",sans-serif;font-size:12px;">          <h2 style="border-bottom:1px solid #DDD;font-size:14px;font-weight:normal;padding:13px 0 10px 8px;"><span style="color: #12ADDB;font-weight: bold;">&gt; </span>系统消息</h2>          <div style="padding:0 12px 0 12px;margin-top:18px">    <p>{content}</p><p>本消息为自动发送，如有疑问，联系邮箱<a style="text-decoration:none; color:#12addb"  href="#" target="_blank">ghwg18@qq.com</a>。</p>          </div>      </div>',
        "summary": summary,  # 消息摘要，显示在微信聊天页面或者模版消息卡片上，限制长度100，可以不传，不传默认截取content前面的内容。
        "contentType": 1,  # 内容类型 1表示文字  2表示html(只发送body标签内部的数据即可，不包括body标签) 3表示markdown
        "uids": [  # 发送目标的UID，是一个数组。注意uids和topicIds可以同时填写，也可以只填写一个。
            uid
        ],
        # "url": "",  # 原文链接，可选参数
        "verifyPay": False  # 是否验证订阅时间，true表示只推送给付费订阅用户，false表示推送的时候，不验证付费，不验证用户订阅到期时间，用户订阅过期了，也能收到。
    }
    res = requests.post(api_url, json=data, timeout=2).json()
    if res['code'] == 1000:  # 推送成功
        logger.info("微信订阅消息发送成功！")
        return True
    else:
        logger.info(f"微信订阅消息发送失败！原因：{res['msg']}")
        return False


# 创建订阅回调消息二维码
def wx_qrcimg(lib: str, data: str):
    """
    :param lib: 生成二维码参数的类型，网站用户绑定通知：user；绑定阳光跑账号：userid
    :param data: 网站用户名 or 阳光跑userid
    :return: 200生成成功二维码地址：json['img'] 400生成失败
    """
    """生成二维码参数"""
    qrc_data = ""
    if lib == "user":  # 用户绑定通知
        qrc_data = f"username:{data}"
    elif lib == "userid":  # 绑定阳光跑通知
        qrc_data = f"userid:{data}"
    else:  # 类别有误
        return {"code": 400, "msg": "生成二维码参数有误，生成失败"}
    """获取数据配置"""
    _cnf = web_class.get_web_config()
    appToken = _cnf['WxAppToken']  # 微信推送通讯密钥
    api_url = 'https://wxpusher.zjiecode.com/api/fun/create/qrcode'
    data = {
        "appToken": appToken,  # 必填，appToken,前面有说明，应用的标志
        "extra": qrc_data,  # 必填，二维码携带的参数，最长64位
        "validTime": 180  # 可选，二维码的有效期，默认30分钟，最长30天，单位是秒
    }
    res = requests.post(api_url, json=data, timeout=2).json()
    if res['code'] == 1000:  # 获取成功了
        return {"code": 200, "img": res['data']['shortUrl']}
    else:  # 生成二维码失败
        return {"code": 400, "msg": "二维码生成失败"}


