# coding=utf-8
import os
from datetime import datetime
from flask import render_template, session, g, request, got_request_exception, redirect, url_for
from flask_apscheduler import APScheduler
from flask_caching import Cache
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFError

import config
from exts import app, limiter, db, search, csrf
from module.blueprint import user_bp, user_imei_bp, user_vip_bp, \
    user_qrc_bp, user_kami_bp, web_bp, app_bp, agent_bp, wxpusher_bp, user_work_bp
from module.mysql.ModuleClass.UserClass import user_class
from module.mysql.ModuleClass.WebClass import web_class
from module.send import sendwxbot, send_wxmsg
from tasks.task_list import Config

# 配置
scheduler = APScheduler()  # 实例化
app.config.from_object(config)  # 载入config配置
app.config.from_object(Config())  # 载入定时任务配置
db.init_app(app)  # 初始化数据库
csrf.init_app(app)  # CSRF保护初始化
search.init_app(app)  # 全局搜索器
cache = Cache(app)  # 缓存配置

migrate = Migrate(app, db)  # 实例化蓝图

# 用户蓝图
app.register_blueprint(user_bp)  # 用户蓝图
app.register_blueprint(web_bp)  # 网站蓝图
app.register_blueprint(user_imei_bp)  # 用户imeicode操作蓝图
app.register_blueprint(user_vip_bp)  # 用户vip操作蓝图
app.register_blueprint(user_qrc_bp)  # QRC扫码登录
app.register_blueprint(user_kami_bp)  # 卡密蓝图
app.register_blueprint(user_work_bp)
# api接口
app.register_blueprint(app_bp)  # app蓝图
app.register_blueprint(wxpusher_bp)  # wxpusher回调接口
# 代理
app.register_blueprint(agent_bp)  # 代理蓝图


# 自定义过滤器
# 切割
def mysplit(value, sep):
    return value.split(sep)


# 将自定义的过滤器添加到 Jinja2 环境中
app.jinja_env.filters['mysplit'] = mysplit  # 切割


# 主站首页
@app.route('/')
@limiter.exempt()
@cache.cached()
def index():
    web_cf = web_class.get_web_config()
    info = {"WebName": web_cf["WebName"]}
    return render_template('index.html', **info)


@app.route('/install')
@limiter.exempt()
def install():
    import subprocess

    from exts import db, app
    from module.mysql.models import WebConfig, Users

    # 定义要执行的命令列表
    commands = ["flask db init", "flask db migrate", "flask db upgrade"]

    # 依次执行每个命令
    for cmd in commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("输出内容：", result.stderr)
        else:
            print("错误信息：", result.stderr)
            return f"安装失败原因：{result.stderr}"
    with app.app_context():
        # 创建网站配置
        webconfig = WebConfig()
        db.session.add(webconfig)
        db.session.commit()
        # 创建管理员账号
        adminuser_data = Users(UserName='admin', Password='123456', Email='123456@qq.com', QQh=123456, UserLib="管理员")
        db.session.add(adminuser_data)
        db.session.commit()
    return '安装成功,默认的管理员账号:admin 123456'


@app.errorhandler(500)
@limiter.exempt()
def pag_error(error):
    return render_template('500.html'), 500


@app.errorhandler(404)
@limiter.exempt()
@app.route('/404')
def page_not_found(error=None):
    return render_template('404.html'), 404


@app.errorhandler(429)
@limiter.exempt()
def limiter_error(error):
    return render_template('erro.html',
                           **{"code": 429, "msg": "error:接口请求限制中..."}), 429


# csrf权限验证界面
@app.errorhandler(CSRFError)
def handler_csrf_error(error):
    return render_template('csrf-error.html'), 400


@app.route('/CsrfError', methods=['GET'])
def csrf_error_index():
    return render_template('csrf-error.html')


# 错误响应信号处理
def log_exception_finished(sender, exception, *args):
    # 获取网站配置
    web_config = web_class.get_web_config()
    # 请求的数据
    _data = request.get_data().decode('utf-8')  # 收到的请求数据
    _method = request.method  # 请求方法：GET/POST
    _url = request.url  # 发送请求的url
    _username = session.get("username")  # 触发错误的用户
    _ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)  # 用户ip
    nr = f"无感阳光跑网站出现500错误！\n错误：{exception}\n请求方法：{_method}\n请求ip：{_ip}\n请求url:{_url}\n收到数据：{_data}\n用户：{_username}"
    sendwxbot(nr)


got_request_exception.connect(log_exception_finished, app)


# # 自定义CORS策略
# @app.after_request
# def add_cors_header(response):
#     response.headers['Access-Control-Allow-Origin'] = '*'  # 允许所有跨域请求
#     response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
#     response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken, X-Csrftoken'
#     return response


# 服务器请求前做的工作
@app.before_request
def before_request():
    session.permanent = True  # 开启session有效期设置
    # 获取用户cookie信息
    username = session.get('username')
    password = session.get('password')
    user_lib = ""  # 用户身份
    if username and password:  # 如果获取到用户信息了
        # 获取用户信息
        user_lib = user_class.get_user_lib(username)  # 用户类别
        # 设置用户信息
        setattr(g, 'username', username)
        setattr(g, 'password', password)
        setattr(g, 'UserLib', user_lib)
    # 每次请求接口前打印接口信息
    _data = request.get_data()
    if str(_data) == "b\'\'":  # 请求信息为空
        pass
    else:
        config.logger.info(f"【收到请求】获取到请求信息：{_data}")

    if "install" not in request.path:
        # 判断网站是否维护 管理员可以访问
        web_config = web_class.get_web_config()
        if not web_config["WebSwitch"]:  # 网站关闭
            if username:  # 已登录用户
                if user_lib != "管理员":  # 不是管理员用户返回维护界面
                    return render_template("weihu.html")
                else:
                    pass
            else:
                if request.method == "POST":  # 对post接口进行返回信息
                    return {"code": 400, "msg": f"网站正在维护中。。。<br>{datetime.now().date()}"}
                else:
                    pass
        else:
            pass


# 上下文处理器
# 给模板传值
@app.context_processor
def context_processor():
    """获取网站配置"""
    web_config = web_class.get_web_config()
    if hasattr(g, 'username'):  # 如果已经登录
        info = {"username": g.username, "UserLib": g.UserLib, "WebConfig": web_config}
        return info
    else:
        return {}


if __name__ == '__main__':
    limiter.init_app(app)  # 初始化限流器
    scheduler.init_app(app)  # 初始化定时任务
    scheduler.start()  # 启动定时任务
    app.run(host="127.0.0.1", port=5100, debug=False)
