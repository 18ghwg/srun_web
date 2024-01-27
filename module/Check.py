# 检测是否登陆
from flask import g, redirect, url_for, render_template, request
from functools import wraps

from module.mysql.ModuleClass.UserClass import user_class


# 登录状态检测
def login_check(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """在cookie中获取信息"""
        username = g.get('username')  # 用户名
        password = g.get('password')  # 密码
        """在数据库获取用户信息"""
        Password = user_class.get_user_password(username)
        if hasattr(g, 'username'):
            if password == Password:  # 如果密码正确
                return func(*args, **kwargs)
            else:
                return redirect(f"{url_for('user.user_login')}?return_to={request.path}")
        else:
            return redirect(f"{url_for('user.user_login')}?return_to={request.path}")

    return wrapper


# 用户权限检测->不是管理员时将返回404界面
def admin_check(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """获取cookie信息"""
        UserName = g.get('username')  # 用户名
        if UserName:  # 读取到cookie信息了
            """获取用户身份"""
            UserLib = user_class.get_user_lib(UserName)
            """用户身份判断"""
            if UserLib == "管理员":
                return func(*args, **kwargs)
            else:
                return render_template('404.html')
        else:
            pass
    return wrapper


# 用户权限检测->不是代理时将返回404界面
def agent_check(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        """获取cookie信息"""
        UserName = g.get('username')  # 用户名
        if UserName:  # 读取到cookie信息了
            """获取用户身份"""
            UserLib = user_class.get_user_lib(UserName)
            """用户身份判断"""
            if UserLib == "代理" or UserLib == "管理员":
                return func(*args, **kwargs)
            else:
                return render_template('404.html')
        else:
            pass
    return wrapper

