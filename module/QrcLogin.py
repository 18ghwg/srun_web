import random
import uuid
from datetime import datetime
from string import ascii_letters, digits
from typing import Union
import httpx
import requests
import re

from config import logger
from module.mysql.ModuleClass.VipClass import vip_class
from module.send import sendwxbot
from module.srun_token import token_get_info

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 11; zh-cn; MI 9 Build/RKQ1.200826.002) AppleWebKit/537.36 (KHTML, "
                  "like Gecko) Version/4.0 Chrome/89.0.4389.116 Mobile Safari/537.36 XiaoMi/MiuiBrowser/16.2.25 "
                  "swan-mibrowser "
}

"""
苹果http://client4.aipao.me/
安卓http://client3.aipao.me/
"""


# 获取登录二维码
def get_qcr_img():
    api = 'https://open.weixin.qq.com/connect/app/qrconnect?appid=wxf83de11533c17d91&&bundleid=com.suntrav.dogand&scope=snsapi_userinfo'
    _headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x6307062c)",
    }

    res = requests.post(url=api, headers=_headers, timeout=5)
    if res.status_code == 200:
        # 提取uuid
        try:
            _uuid = re.findall('uuid: "(.*?)",', res.text)[0]
        except KeyError:
            sendwxbot("正则提取uuid失败")
            return {}
        else:
            img_url = f'https://open.weixin.qq.com/connect/qrcode/{_uuid}'
            return {"uuid": _uuid, "img_url": img_url}
    else:
        sendwxbot(f"【获取阳光跑二维码】请求失败，状态码：{res.status_code}")
        return {}


# 检测登录状态并获取token
def check_login_state(user_uuid: str, mod: str):
    """
    :param user_uuid: 阳光跑userid
    :param mod: 操作的方法：AddVip or QrcLogin
                如果是AddVip不会对vip用户返回IMEICode
    :return: 登陆失败：False2
    """
    api = f'https://long.open.weixin.qq.com/connect/l/qrconnect?uuid={user_uuid}&f=url'
    res = requests.get(api, headers)
    if res.status_code == 200:
        state_code = int(re.findall('window.wx_errcode=(.*?);', res.text)[0])  # 状态码
        if state_code == 405:  # 登录成功
            code = re.findall('\?code=(.*?)&state=', res.text)[0]  # 登录代码
            _imei = str(uuid.uuid4())
            _rk = "".join([random.choice(ascii_letters + digits) for _ in range(0, 32)])
            api = f'http://client3.aipao.me/api/{_rk}/QM_Users/Login_Android?wxCode={code}&IMEI=Android:{_imei}'
            res = requests.get(api, headers).json()
            if res['Success']:  # 登陆成功
                """获取登录成功返回信息"""
                IMEICode = res['Data']['IMEICode']  # IMEICode
                userid = res['Data']['UserId']  # UserID
                token = res['Data']['Token']  # Token
                _info = token_get_info(token)  # token获取信息
                if isinstance(_info, dict):
                    name = _info.get('name')  # 姓名
                else:  # 获取信息失败
                    return False
                """获取vip信息"""
                vip_lib = vip_class.get_vip_lib(userid)  # 获取vip类型
                viped_date = vip_class.get_viped_date(userid)  # vip到期时间
                vip_num = vip_class.get_vip_run_num(userid)  # 获取vip剩余跑步次数
                if (vip_lib == "扫码" and mod == "QrcLogin") and (viped_date >= datetime.now() or vip_num >= 1):
                    # 扫码用户并且需要返回IMEICode
                    # 扫码vip未到期或者有跑步次数
                    return {"code": 200, "IMEICode": IMEICode}  # 返回IMEICode
                else:
                    """获取用户信息"""
                    user_info = token_get_info(token)
                    return {"code": 405, "msg": f"登录成功-你的信息："
                                                f"<br>姓名：{user_info['name']}"
                                                f"<br>学校：{user_info['school']}"
                                                f"<br>UserId:{user_info['userid']}"
                                                f"<br>请继续输入卡密操作",
                            "name": user_info['name'],
                            "school": user_info['school'],
                            "userid": user_info['userid'],
                            "token": token}
            else:  # 登陆失败
                return False
        else:  # 登录失败
            return {"code": state_code, "msg": rt_msg(state_code)}
    else:  # 请求失败
        return False


def rt_msg(state_code: int):
    if state_code == 408:
        return "等待扫码ing..."
    elif state_code == 404:
        return "已扫码，正在等待登录..."



