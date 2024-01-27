# -*- coding: utf-8 -*-
"""
@Time    : 2022/12/30 20:25
@Author  : ghwg
@File    : Web.py

"""
from flask import Blueprint, session, request, render_template

from module.Check import login_check, admin_check
from module.mysql.ModuleClass.WebClass import web_class

web_bp = Blueprint('web', __name__, url_prefix='/User')


# 网站基本信息配置
@web_bp.route('/Web/SetInfo', methods=['GET', 'POST'])
@login_check
@admin_check
def web_info_set():
    if request.method == "GET":
        """获取网站配置"""
        WebConfig = web_class.get_web_config()
        return render_template('user/pag/web/WebInfoSet.html', **WebConfig)
    else:
        """接收post参数"""
        _post = request.form.to_dict()
        try:
            """基本信息"""
            WebName = _post["web_name"]
            WebUrl = _post["web_url"]
            WebGG = _post["web_gg"]
            KamiPayUrl = _post["kami_pay_url"]
            Managers = _post["managers"]
            WebSwitch = int(_post["web_switch"])
            """邮件"""
            SendEmailMaxNum = _post["send_email_max_num"]
            """企业微信"""
            CorpID = _post["corp_id"]
            AccessToken = _post["access_token"]
            AgentID = _post["agent_id"]
            CorpSecret = _post["corp_secret"]
            """微信订阅"""
            WxAppToken = _post["wx_app_token"]
            """用户设置"""
            UserLoginFailMaxNum = _post["user_login_fail_max_num"]
            UserCheckCreditNum = _post["user_check_credit_num"]
            """跑步设置"""
            BCVipedDay = _post["bc_viped_day"]
            BCVipRunNum = _post["bc_vip_run_num"]
            """代理设置"""
            AgentWebGG = _post.get("agent_web_gg")
            """APP设置"""
            AndroidAppDownloadUrl = _post.get("android_download_url")
            AndroidAppVersion = _post.get("android_version")
            AndroidAppUpContext = _post.get("android_upcontext")
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """构造字典"""
            WebInfo = {
                "WebName": WebName,
                "WebUrl": WebUrl,
                "WebGG": WebGG,
                "Managers": Managers,
                "WebSwitch": WebSwitch,
                "KamiPayUrl": KamiPayUrl,
                "SendEmailMaxNum": SendEmailMaxNum,
                "CorpID": CorpID,
                "AccessToken": AccessToken,
                "AgentID": AgentID,
                "CorpSecret": CorpSecret,
                "WxAppToken": WxAppToken,
                "UserLoginFailMaxNum": UserLoginFailMaxNum,
                "UserCheckCreditNum": UserCheckCreditNum,
                "BCVipedDay": BCVipedDay,
                "BCVipRunNum": BCVipRunNum,
                "AgentWebGG": AgentWebGG,
                "AndroidAppDownloadUrl": AndroidAppDownloadUrl,
                "AndroidAppVersion": AndroidAppVersion,
                "AndroidAppUpContext": AndroidAppUpContext,
            }
            return web_class.put_web_info(WebInfo)
