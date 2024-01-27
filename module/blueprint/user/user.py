# -*- coding: utf-8 -*-
"""
@Time    : 2022/12/9 9:28
@Author  : ghwg
@File    : user.py
用户蓝图
"""
import json

from flask import Blueprint, request, render_template, session, redirect, url_for, abort, make_response
from flask_wtf.csrf import validate_csrf

from exts import limiter, redis_client
from module.Check import login_check, admin_check
from module.QQLogin import qq_login_class
from module.mysql.ModuleClass.EmailClass import email_class
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.ModuleClass.WebClass import web_class
from module.send import wx_qrcimg
from ..Forms import RegisterForm, SendEmailCode
from ...VCode import ImageCode

user_bp = Blueprint('user', __name__, url_prefix='/User')


# 用户注册
@user_bp.route('/Register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'GET':
        return render_template('user/register.html')
    else:
        form = RegisterForm(request.form)
        if form.validate():
            _post = request.form.to_dict()  # post信息
            """获取post信息"""
            try:
                username = _post.get('username')  # 账号
                password = _post.get('password')  # 密码
                qqh = int(_post.get('qqh'))  # QQ号
                email = _post.get('email')  # 邮箱
            except KeyError or ValueError:
                return {"code": 500, "msg": "参数有误,请检查表单内容格式是否有误"}
            else:
                """开始注册"""
                register_date = user_class.user_register(
                    **{
                        "username": username,
                        "password": password,
                        "email": email, "qqh": qqh
                    })
                return register_date
        else:
            errors = {field.name: field.errors for field in form if field.errors}
            return {"code": 400, "errors": errors}


# 用户登录
@user_bp.route('/Login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'GET':
        if session.get('usename'):  # 已登录->直接跳转后台
            return redirect(url_for('user.user_index'))
        else:
            return_to = request.args.get('return_to')  # 跳转的地址
            # 获取网站配置
            web_cf = web_class.get_web_config()
            info = {"WebName": web_cf["WebName"], "ReturnTo": return_to}
            return render_template('user/login.html', **info)
    elif request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        img_code = request.form.get("img_code").lower()  # 验证码
        """判断用户登录失败次数是否上限"""
        UserLoginFailMaxNum = web_class.get_web_config()["UserLoginFailMaxNum"]  # 用户登录失败上限
        UserLoginFailNum = user_class.get_user_login_fail_num(username)  # 获取登陆失败次数
        """校验验证码"""
        cache_img_code = redis_client.get('img_code')  # 缓存的验证码
        if not cache_img_code:
            return {"code": 204, "msg": "验证码已过期，请重新获取！"}
        elif cache_img_code.decode('utf-8') != img_code:
            return {"code": 205, "msg": "验证码不正确，请检查后填写！"}
        else:  # 验证码校验正确
            pass
        if UserLoginFailNum < UserLoginFailMaxNum:  # 未超出登录失败上限
            if user_class.check_user_login(username, password):  # 账号密码校验成功
                # 设置session信息
                session['username'] = username
                session['password'] = password
                return {"code": 200, "msg": "登录成功."}
            else:
                """增加登录失败次数"""
                user_class.add_user_fail_num(username)
                UserLoginFailNumNow = user_class.get_user_login_fail_num(username)  # 用户当前的登录是失败次数
                return {"code": 203, "msg": f"账号或密码错误,你还有{UserLoginFailMaxNum - UserLoginFailNumNow}次尝试机会。"}
        else:
            return {"code": 202, "msg": f"登录是失败次数超出上限{UserLoginFailMaxNum}次,账号已被锁定,你可以找回密码解锁账号!"}
    else:
        return {"code": 201, "msg": "异常请求."}


# 登录验证码
@user_bp.route('/LoginVcode', methods=['GET'])
@limiter.exempt()
def login_vcode():
    bstring, code = ImageCode().draw_verify_code()
    response = make_response(bstring.getvalue())
    response.headers['Content-Type'] = 'image/jpeg'
    # session['vcode'] = code.lower()  # 验证码保存在session中
    redis_client.setex('img_code', 300, code)  # 将验证码 code 保存到 Redis 中，并设置过期时间为 300 秒
    return response


# 发送密码重置邮件
@user_bp.route('/SendRePWMail', methods=["GET", "POST"])
def send_reset_password_mail():
    if request.method == 'GET':
        return render_template('user/SendRePasswordMail.html')
    else:
        """获取post信息"""
        _post = request.form.to_dict()
        try:
            email = _post['email']
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            return email_class.send_reset_password_email(email)  # 发送重置密码邮件


# 重置用户密码
@user_bp.route('/password/token/<string:Token>', methods=["GET", "POST"])
def re_password(Token):
    if request.method == 'GET':
        """判断要是否存在"""
        if user_class.check_repassword_token(Token):
            return render_template('user/ResetPassword.html')
        else:
            return render_template('404.html')
    else:
        form = request.form
        if form.values():
            """获取post信息"""
            _post = request.form.to_dict()
            try:
                password = _post['password']
            except KeyError:
                return {"code": 500, "msg": "参数有误"}
            else:
                return user_class.reser_user_password(Token, password)  # 重置密码
        else:
            errors = {field.name: field.errors for field in form if field.errors}
            return {"code": 400, "errors": errors}


# 发送验证码
@user_bp.route('/SendMailCode', methods=['POST'])
def send_mail_code():
    form = SendEmailCode(request.form)
    if form.validate():
        _post = request.form.to_dict()  # 获取post参数
        return email_class.send_emailcode(_post['email'])
    else:
        errors = {field.name: field.errors for field in form if field.errors}
        return {"code": 400, "errors": errors}


# 退出登录
@user_bp.route('/Logout', methods=['GET'])
def user_logout():
    session.clear()  # 清理cookie
    return redirect(url_for('user.user_login'))


# 用户后台首页
@user_bp.route('/Index', methods=['GET'])
@limiter.exempt()
@login_check
def user_index():
    """获取代理账号信息"""
    UserName = session.get("username")
    """获取后台数据"""
    info = user_class.user_get_index_info(UserName)
    return render_template('user/index.html', **info)


# 获取用户后台数据
@user_bp.route('/Ajax/Info', methods=['POST'])
@login_check
@limiter.exempt()
def ajax_info():
    """获取cookie信息"""
    UserName = session.get('username')
    return user_class.user_get_index_info(UserName)


# 获取用户消息
@user_bp.route('/UnredMessages', methods=['POST', 'GET'])
@login_check
@limiter.exempt()
def get_unred_msg():
    # 获取session信息
    username = session.get('username')  # 用户名
    # 获取用户未读消息
    return user_class.get_user_message(username)


# 获取用户签到状态
@user_bp.route('/GetUserCheckState', methods=['POST'])
@login_check
def get_user_check_state():
    # 获取session信息
    username = session.get('username')  # 用户名
    return user_class.get_user_check_state(username)


# 用户修改信息
@user_bp.route('/Info', methods=['GET', 'POST'])
@login_check
def user_info():
    """获取用户信息"""
    UserName = session.get("username")  # 用户名
    if request.method == 'GET':
        """获取用户信息"""
        UserInfo = user_class.get_user_info(UserName)
        return render_template('user/pag/UserInfo.html', **UserInfo)
    else:
        """获取post信息"""
        _post = request.form.to_dict()
        try:
            Password = _post["password"]
            QQh = _post["qqh"]
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            info = {
                "UserName": UserName,
                "QQh": QQh,
                "Password": Password,
            }
            return user_class.put_user_info(info)


# 获取用户头像
@user_bp.route('/ico', methods=['GET'])
@limiter.exempt()
@login_check
def get_user_ico():
    """获取用户信息"""
    UserName = session.get("username")
    _info = user_class.get_user_info(UserName)
    if _info:  # 获取到用户信息
        user_qqh = _info["QQh"]
    else:
        user_qqh = 123456
    api_url = f'http://q2.qlogo.cn/headimg_dl?dst_uin={user_qqh}&spec=100'
    return redirect(api_url)


# 获取wx公众号订阅二维码
@user_bp.route('/wximg', methods=['POST'])
@login_check
def get_wx_qrcimg():
    """获取用户信息"""
    UserName = session.get("username")
    """生成订阅二维码"""
    return wx_qrcimg("user", UserName)


# 微信订阅设置
@user_bp.route('/SubWxMsg', methods=['GET'])
@login_check
def sub_wx_msg():
    """获取cookie信息"""
    UserName = session.get("username")
    """获取用户信息"""
    _info = user_class.get_user_info(UserName)
    return render_template("user/pag/SubWxMsg.html", **_info)


# 查询用户微信订阅状态
@user_bp.route('/CheckWxSubState', methods=['POST'])
@login_check
def check_wx_sub_state():
    """获取cookie信息"""
    UserName = session.get("username")
    """获取用户数据库信息"""
    _info = user_class.get_user_info(UserName)
    uid = _info.get("WxUid")  # 订阅uid
    if uid:  # 订阅id设置成功
        return {"code": 200, "data": {"uid": uid}}
    else:  # 没有订阅
        return {"code": 400, "msg": "未能成功订阅"}


# 用户列表
@user_bp.route('/UserList', methods=['GET', 'POST'])
@login_check
@admin_check
@limiter.exempt()
def user_list():
    """获取session信息"""
    UserName = session.get("username")
    """获取账号信息"""
    if request.method == "GET":
        return render_template("user/pag/user/UserList.html")
    else:  # post获取账号列表
        """获取post信息"""
        _post = json.loads(request.data)
        try:
            page = _post["page"]
            offset = _post["offset"]
            limit = _post["limit"]
            search = _post.get('search')  # 搜索数据的关键词
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """切片处理账号数据"""
            users_list = user_class.get_user_list(UserName, search)
            users_list['rows'] = users_list['rows'][int(offset):int(limit) * int(page)]
            return users_list


# 修改用户信息
@user_bp.route('/SetUserInfo', methods=['GET', 'POST'])
@login_check
@admin_check
@limiter.exempt()
def set_user_info():
    """获取代理账号"""
    if request.method == 'GET':
        """获取get参数"""
        UserName = request.args.get('UserName')
        info = user_class.get_user_info(UserName)  # 获取用户信息
        return render_template('user/pag/user/SetUserInfo.html', **info)
    else:
        """获取post信息"""
        _post = request.form.to_dict()
        try:
            UserName = _post['user_name']
            info = {
                "Password": _post["password"],
                "QQh": _post["qqh"],
                "UserLib": _post["user_lib"],
            }
            if _post["email"]:  # 填写邮箱了
                info.update({"Email": _post["email"]})
            else:
                info.update({"Email": None})
            if _post["wxuid"]:  # 填写微信订阅uid了
                info.update({"WxUid": _post["wxuid"]})
            else:
                info.update({"WxUid": None})
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            """修改数据库信息"""
            return user_class.put_user_info_admin(UserName, info)


# 删除用户
@user_bp.route('/DelUser', methods=['POST'])
@login_check
@admin_check
@limiter.exempt()
def del_user():
    """获取post参数"""
    DelUserNameList = []  # 删除用户列表
    try:
        _post = request.form.to_dict()
        try:
            DelUserNameList = _post['UserName'].split(',')
        except IndexError:  # 单删
            DelUserNameList.append(_post["UserName"])
    except KeyError:
        return {"code": 500, "msg": "参数有误！"}
    else:
        return user_class.del_user(DelUserNameList)  # 删除IMEICode


# 用户绑定QQ
@user_bp.route('/BindingQQ', methods=['GET', 'POST'])
@login_check
@limiter.exempt()
def binding_qq():
    username = session.get('username')  # 账号
    code = request.args.get('code')
    if code:  # 获取到code了
        # 获取access_token
        access_token = qq_login_class.get_access_token(code, 'login')
        if access_token:  # 获取到了
            # 获取用户OpenId
            openid = qq_login_class.get_open_id(access_token)
            if openid:
                # 获取用户信息
                _user_info = qq_login_class.get_user_info(access_token, openid)
                if isinstance(_user_info, dict):  # 成功获取到昵称和头像信息
                    if user_class.up_user_openid(username, openid):  # 上传QQopenid成功
                        return redirect(url_for('user.binding_qq'))  # 跳转绑定界面
                    else:
                        info = {"code": 400, "msg": "该QQ号已授权至本站其他用户,请先解绑后在操作"}
                        return render_template('user/pag/BindingQQ.html', **info)
                else:  # 过去用户信息失败
                    info = {"code": 400, "msg": "获取用户信息失败"}
                    return render_template('user/pag/BindingQQ.html', **info)
            else:  # 登录失败
                info = {"code": 400, "msg": "openid获取失败"}
                return render_template('user/pag/BindingQQ.html', **info)
        else:
            info = {"code": 400, "msg": "access_token获取失败"}
            return render_template('user/pag/BindingQQ.html', **info)
    else:  # get界面
        # 获取用户信息
        info = user_class.get_user_info(username)
        return render_template('user/pag/BindingQQ.html', **info)


# 解除用户QQ绑定
@user_bp.route('/RelieveBinding', methods=['POST'])
@login_check
def relieve_binding():
    # 获取session信息
    username = session.get('username')
    # 解除用户绑定QQ
    if user_class.relieve_binding(username):
        return {"code": 200, "msg": "QQ绑定已解除"}
    else:
        return {"code": 400, "msg": "QQ解绑失败"}


# QQ互联授权登录
@user_bp.route('/QQLogin', methods=['GET', 'POST'])
def qq_login():
    # 获取get参数
    code = request.args.get('code')  # 登录返回的code
    if not code:
        return render_template('erro.html',
                               **{"code": 500, "msg": "登录失败, erro: 获取登录参数出错"})
    else:
        # 获取access_token
        access_token = qq_login_class.get_access_token(code, 'login')
        if access_token:  # 获取到了
            # 获取用户OpenId
            openid = qq_login_class.get_open_id(access_token)
            if openid:
                # 获取用户信息
                _user_info = qq_login_class.get_user_info(access_token, openid)
                if isinstance(_user_info, dict):  # 成功获取到昵称和头像信息
                    # 获取用户账号密码
                    user_data = user_class.use_openid_get_username_and_password(openid)
                    if isinstance(user_data, dict):  # openid匹配成功
                        username = user_data.get('username')  # 账号
                        password = user_data.get('password')  # 密码
                        # 记录session
                        session['username'] = username
                        session['password'] = password
                        # 跳转用户后台
                        return redirect(url_for('user.user_index'))
                    else:  # 没有用户绑定QQ

                        return render_template('erro.html',
                                               **{"code": 400, "msg": "该QQ未绑定本站账号,请先到后台-个人信息-绑定QQ后使用快捷登录"})
                else:  # 过去用户信息失败
                    return render_template('erro.html',
                                           **{"code": 400, "msg": "获取用户信息失败"})
            else:  # 登录失败
                return render_template('erro.html',
                                       **{"code": 400, "msg": "openid获取失败"})
        else:
            return render_template('erro.html',
                                   **{"code": 400, "msg": "access_token获取失败"})


# 用户签到领积分
@user_bp.route("/Check", methods=["POST"])
@login_check
def user_check():
    # session获取用户信息
    username = session.get("username")
    # 开始签到
    return user_class.user_check(username)


# 检测用户是否存在
@user_bp.route('/CheckUserExistence', methods=['POST'])
@login_check
def check_user_existence():
    form = request.form.to_dict()
    UserName = form['UserName']
    return user_class.check_user_existence(UserName)


# 系统日志
@user_bp.route("/SystemLog", methods=['POST', 'GET'])
@login_check
def system_log():
    """获取session参数"""
    UserName = session.get('username')  # 用户名
    if request.method == "GET":
        return render_template("user/pag/SystemLog.html")
    else:
        """获取post信息"""
        _post = json.loads(request.data)
        try:
            search = _post.get("search")
            page = _post["page"]
            offset = _post["offset"]
            limit = _post['limit']
        except KeyError:
            return {"code": 500, "msg": "参数有误"}
        else:
            print(search)
            """切片处理账号数据"""
            log_list = user_class.get_user_system_log(UserName, search)
            log_list['rows'] = log_list['rows'][int(offset):int(limit) * int(page)]
            return log_list

