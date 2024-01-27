import json
import requests

from config import logger

API_ROOT = 'http://client3.aipao.me/api'  # API


# token获取信息
def token_get_info(token):
    """
    :param token: 阳光跑token
    :return: 包含name、school、userid的字典 or False
    """
    # 检测token
    res = requests.get(url=f"{API_ROOT}/{token}/QM_Users/GS",
                       headers={'version': '2.45', 'auth': 'ABISHvbZgUKtJ/3SO1XqeFQ=='})
    res = json.loads(res.text)
    if res["Success"]:
        mz = res["Data"]["User"]["NickName"]
        school = res["Data"]["SchoolRun"]["SchoolName"]
        userid = res["Data"]["User"]["UserID"]
        return {"name": mz, "school": school, "userid": userid}
    else:
        return False


# IMEI获取token信息
def get_imei_info(token: str):
    """
    :param token: token
    :return: False：账号无效  否则返回姓名、学校、userid
    """
    # Login
    TokenRes = requests.get(
        API_ROOT + '/%7Btoken%7D/QM_Users/Login_AndroidSchool?IMEICode=' + token,
        headers={"version": "2.40", "auth": "ABISHvbZgUKtJ/3SO1XqeFQ=="})
    TokenJson = json.loads(TokenRes.content.decode('utf8', 'ignore'))
    if not TokenJson['Success']:  # token无效
        _token_get_info = token_get_info(token)
        if isinstance(_token_get_info, dict):  # 如果是传过来的是token（一般是代理网站首页添加vip传过来的token）
            return _token_get_info
        else:
            return False
    else:
        # 获取账号信息开始
        token = TokenJson['Data']['Token']
        check_json = requests.get('http://client3.aipao.me/api/' + token + '/QM_Users/GS',
                                  headers={'version': '2.42', 'auth': 'ABISHvbZgUKtJ/3SO1XqeFQ=='}).json()
        schoolRes = requests.get(
            API_ROOT + '/' + token + '/QM_Users/GS', headers={"version": "2.45", 'auth': 'ABISHvbZgUKtJ/3SO1XqeFQ=='})
        schoolJson = json.loads(schoolRes.content.decode('utf8', 'ignore'))
        # logger.info(schoolJson)
        try:
            school = schoolJson['Data']['SchoolRun']['SchoolName']  # 获取学校
            mz = check_json['Data']['User']['NickName']  # 获取姓名
            userid = check_json['Data']['User']['UserID']  # 获取账号id
        except KeyError:
            return {"name": "获取信息失败,联系网站管理员", "school": "获取信息失败,联系网站管理员", "userid": "获取信息失败,联系网站管理员"}
        return {"name": mz, "school": school, "userid": userid}




if __name__ == '__main__':
    print(token_get_info('ca1abb12ebbe455c88a71e07b35a1cf9'))