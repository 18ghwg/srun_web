# -*- coding: utf-8 -*-
"""
@Time    : 2023/1/1 16:37
@Author  : ghwg
@File    : App.py

"""
from flask import Blueprint, request, url_for, redirect

from exts import limiter, csrf
from module.mods import check_email
from module.mysql.ModuleClass.IMEICodeClass import imei_class
from module.mysql.ModuleClass.WebClass import web_class


app_bp = Blueprint('app', __name__, url_prefix='/api/app')


# APP提交账号
@app_bp.route('/AddIMEICode', methods=['POST'])
@limiter.exempt()
@csrf.exempt
def imei_add():
    """获取post信息"""
    _post = request.form.to_dict()
    try:
        IMEICode = _post['IMEICode']
        Email = _post['Email']
        RunTime = _post['RunTime']
        User = _post['UserName']
    except KeyError:
        return {"code": 500, "msg": "参数有误"}
    else:
        """参数格式校验"""
        if check_email(Email):
            if '=' not in IMEICode:
                info = {
                    "IMEICode": IMEICode,
                    "Email": Email,
                    "RunTime": RunTime,
                    "User": User,
                }
                return imei_class.user_add_imei(info)
            else:
                return {"code": 207, "msg": "请截取等于号后面的字符"}
        else:
            return {"code": 206, "msg": "请输入QQ数字邮箱"}


# 网站配置
@app_bp.route('/config', methods=['GET'])
@limiter.exempt()
@csrf.exempt
def app_config():
    """获取网站配置"""
    web_config = web_class.get_web_config()
    KamiPayUrl = web_config.get('KamiPayUrl')
    AndroidAppVersion = web_config.get('AndroidAppVersion')  # 安卓软件版本号
    AndroidAppDownloadUrl = web_config.get('AndroidAppDownloadUrl')  # 安卓软件下载链接
    AndroidAppUpContext = web_config.get('AndroidAppUpContext')  # 软件更新内容
    return {"code": 200, "data": {"kami_pay_url": KamiPayUrl,
                                  "AndroidAppVersion": AndroidAppVersion,
                                  "AndroidAppDownloadUrl": AndroidAppDownloadUrl,
                                  "AndroidAppUpContext": AndroidAppUpContext},
            "WebApi": web_config.get("WebUrl")}


