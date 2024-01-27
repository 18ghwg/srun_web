# -*- coding: utf-8 -*-
"""
@Time    : 2023/1/29 13:02
@Author  : ghwg
@File    : QQLogin.py

"""
from typing import Union

import requests
from flask import url_for

""" QQ互联登录方法 """


class QQLogin:

    # 获取access_token
    @classmethod
    def get_access_token(cls, code: str, mod: str) -> Union[str, None]:
        redirect_url = ''  # 重定向地址
        if mod == 'login':
            redirect_url = f'https://srun.vip{url_for("user.qq_login")}'
        else:
            redirect_url = f'https://srun.vip{url_for("user.binding_qq")}'
        api_url = 'https://graph.qq.com/oauth2.0/token'
        data = {
            "grant_type": "authorization_code",
            "client_id": 102039224,
            "client_secret": "JYbR3Rn24sSowrY2",
            "code": code,
            "redirect_uri": redirect_url,
            "fmt": "json"
        }
        res = requests.get(url=api_url, params=data).json()
        if res.get('error'):  # 获取access_token失败
            return None
        else:
            return res['access_token']

    # 获取openid
    @classmethod
    def get_open_id(cls, access_token: str) -> Union[str, None]:
        api_url = f'https://graph.qq.com/oauth2.0/me'
        get_data = {
            "access_token": access_token,
            "fmt": "json"
        }
        openid_res = requests.get(url=api_url, params=get_data).json()
        if not openid_res.get('code'):  # 没报错
            open_id = openid_res['openid']  # OpenId
            return open_id
        else:  # 获取OpenId失败
            return None

    # 获取登录用户的昵称、头像、性别
    @classmethod
    def get_user_info(cls, access_token: str, open_id: str) -> Union[str, dict]:
        api_url = 'https://graph.qq.com/user/get_user_info'
        get_data = {
            "access_token": access_token,
            "openid": open_id,
            "oauth_consumer_key": 102039224
        }
        res_info = requests.get(url=api_url, params=get_data).json()
        if res_info['ret'] == 0:
            # 获取用户信息
            qq_name = res_info['nickname']  # QQ昵称
            ico_url = res_info['figureurl_qq_2']  # QQ头像 100*100
            return {"qq_name": qq_name, "ico_url": ico_url}
        else:  # 错误-返回响应信息
            return res_info['msg']


qq_login_class = QQLogin()



