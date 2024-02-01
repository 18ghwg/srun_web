import json

from exts import db
from datetime import datetime, time
from jieba.analyse.analyzer import ChineseAnalyzer


# 转json格式
def to_json(inst, cls):
    d = dict()
    '''
    获取表里面的列并存到字典里面
    '''
    for c in cls.__table__.columns:
        v = getattr(inst, c.name)
        if isinstance(v, datetime):  # datetime格式转换
            v = datetime.strftime(v, '%Y-%m-%d %H:%M:%S')
        if isinstance(v, time):  # time格式str转换
            v = time.strftime(v, '%H:%M:%S')
        d[c.name] = v
    return json.loads(json.dumps(d, ensure_ascii=False))


# 配置
class WebConfig(db.Model):
    __tablename__ = 'WebConfig'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    WebName = db.Column(db.String(50), nullable=False, comment="网站名称", default="网站名称")
    Managers = db.Column(db.String(200), nullable=False, comment="管理员账号id, QQ号或者频道id", default="管理员账号id, QQ号或者频道id")
    WebUrl = db.Column(db.String(200), nullable=False, comment="网站url", default="网站url")
    EmailGG = db.Column(db.Text(255), nullable=False, default="邮箱公告", comment="邮件公告")
    CorpID = db.Column(db.String(200), nullable=False, comment="企业微信ID", default="企业微信ID")
    AccessToken = db.Column(db.Text(200), nullable=False, comment="企业微信token", default="企业微信token")
    AgentID = db.Column(db.String(200), nullable=False, comment="企业微信应用ID", default="企业微信应用ID")
    CorpSecret = db.Column(db.String(200), nullable=False, comment="企业微信应用密钥", default="企业微信应用密钥")
    SendEmailMaxNum = db.Column(db.Integer, nullable=False, comment="验证邮件的最大发送次数", default="5")
    WebGG = db.Column(db.String(200), nullable=False, comment="网站公告", default="网站公告")
    PutDate = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="公告更新时间")
    KamiPayUrl = db.Column(db.String(200), nullable=False, comment="卡密购买地址", default="卡密购买地址")
    WxAppId = db.Column(db.Integer, nullable=False, comment="wxpusher应用id", default="123")
    WxAppToken = db.Column(db.String(200), nullable=False, comment="微信推送订阅密钥", default="微信推送订阅密钥")
    UserLoginFailMaxNum = db.Column(db.Integer, nullable=False, default=5, comment="3")
    UserCheckCreditNum = db.Column(db.Integer, nullable=False, default=1, comment="1")
    BCVipedDay = db.Column(db.Integer, nullable=False, default=2, comment="自动检测今日未跑用户自动补偿的vip天数")
    BCVipRunNum = db.Column(db.Integer, nullable=False, default=2, comment="自动检测今日未跑用户自动补偿的vip跑步次数")
    AgentWebGG = db.Column(db.String(100), comment="代理网站首页公告")
    WebSwitch = db.Column(db.Integer, nullable=False, default=1, comment="网站全局开关0关闭1打开")
    AndroidAppVersion = db.Column(db.Integer, default=0, comment="安卓APP软件版本号")
    AndroidAppDownloadUrl = db.Column(db.TEXT(225), comment="安卓APP下载链接", default="安卓APP下载链接")
    AndroidAppUpContext = db.Column(db.String(255), comment="软件更新内容", default="软件更新内容")

    @property
    def json(self):
        return to_json(self, self.__class__)


# WxPusher用户id表
class WxPusher(db.Model):
    __tablename__ = 'WxPusher'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    WxUid = db.Column(db.String(150), comment="微信消息推送用户id")
    UserId = db.Column(db.Integer, nullable=False, comment="阳光跑userid")
    Time = db.Column(db.DateTime, default=datetime.now, comment="加入的时间")

    @property
    def json(self):
        return to_json(self, self.__class__)


# 用户列表
class Users(db.Model):
    __tablename__ = 'Users'
    __searchable__ = ['UserName', 'Email', 'QQh', 'AdminUser', "UserLib"]
    __msearch_analyzer__ = ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    UserName = db.Column(db.String(255), nullable=False, unique=True, comment="用户名")
    Password = db.Column(db.String(255), nullable=False, comment="密码")
    Email = db.Column(db.String(255), nullable=False, unique=True, comment="邮箱")
    WxUid = db.Column(db.String(150), comment="微信消息推送用户id")
    QQh = db.Column(db.String(255), nullable=False, comment="QQ号")
    OpenId = db.Column(db.String(70), nullable=True, comment="QQ登录的用户ID")
    Credit = db.Column(db.Integer, nullable=False, default=0, comment="用户积分")
    CheckState = db.Column(db.Integer, nullable=False, default=0, comment="签到状态,1:已签到；0:未签到")
    CheckDate = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="签到的时间")
    AdminUser = db.Column(db.String(50), default="admin", comment="上级用户名")
    LoginFailNum = db.Column(db.Integer, nullable=False, default=0, comment="登录失败次数")
    UserLib = db.Column(db.String(20), nullable=False, default="普通用户", comment="用户身份")
    AgentQuota = db.Column(db.Integer, nullable=False, default=0, comment="添加代理的额度")
    Time = db.Column(db.DateTime(), nullable=False, default=datetime.now, comment="注册时间")

    def update(self, data):
        for key, value in data.items():
            setattr(self, key, value)
        db.session.add(self)

    @property
    def json(self):
        return to_json(self, self.__class__)


# 代理网站表
class Agent(db.Model):
    __tablename__ = 'Agent'
    __searchable__ = ['AgentUser', 'WebKey', 'Kfqq']
    __msearch_analyzer__ = ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    AgentUser = db.Column(db.String(255), nullable=False, unique=True, comment="用户名")
    WebKey = db.Column(db.String(255), nullable=False, unique=True, comment="代理网站密钥，用于区分")
    WebName = db.Column(db.String(100), nullable=False, comment="代理网站名称")
    Kfqq = db.Column(db.String(255), nullable=False, comment="代理网站客服QQ")
    WebGG = db.Column(db.Text(200), nullable=False, default="网站首页公告", comment="网站首页公告")
    QQGroup = db.Column(db.String(50), nullable=False, comment="QQ群加群链接")

    @property
    def json(self):
        return to_json(self, self.__class__)


# 用户注册验证码表
class Register(db.Model):
    __tablename__ = 'Register'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    Email = db.Column(db.String(255), nullable=False, unique=True, comment="邮箱")
    Code = db.Column(db.Integer, nullable=False, comment="验证码")
    SendNum = db.Column(db.Integer, nullable=False, default=1, comment="发送验证码的次数")
    Time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="发送验证码时间")

    @property
    def json(self):
        return to_json(self, self.__class__)


# 找回密码验证表
class ResetPassword(db.Model):
    __tablename__ = 'ResetPassword'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    Token = db.Column(db.String(200), nullable=False, comment="密码找回密钥,放在url中区分用户")
    UserName = db.Column(db.String(60), nullable=False, comment="用户名")
    Email = db.Column(db.String(50), nullable=False, comment="邮箱")
    Time = db.Column(db.DateTime, default=datetime.now, nullable=False, comment="发送重置密码邮件的时间")

    @property
    def json(self):
        return to_json(self, self.__class__)


# IMEICode列表
class IMEICodes(db.Model):
    __tablename__ = 'IMEICodes'
    __searchable__ = ["IMEICode", "UserId", "Name", "School", "Email", "User", "VipLib", "RunTime"]
    __msearch_analyzer__ = ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    IMEICode = db.Column(db.String(255), nullable=False, unique=True, comment="IMEICode")
    RunTime = db.Column(db.Time, nullable=False, comment="跑步时间")
    UserId = db.Column(db.Integer, nullable=False, comment="阳光跑userid")
    Name = db.Column(db.String(50), nullable=False, comment="姓名")
    School = db.Column(db.String(100), nullable=False, comment="学校")
    Email = db.Column(db.String(255), comment="收件箱")
    WxUid = db.Column(db.String(150), comment="微信消息推送用户id")
    User = db.Column(db.String(100), nullable=False, comment="网站账号")
    VipLib = db.Column(db.String(50), nullable=False, comment="VIP类型")
    VipedDate = db.Column(db.DateTime, nullable=False, comment="vip到期时间")
    VipRunNum = db.Column(db.Integer, nullable=False, comment="vip剩余跑步次数")
    State = db.Column(db.Integer, nullable=False, default=1, comment="IMEICode状态，1有效0无效")
    RunNum = db.Column(db.Integer, nullable=False, default=0, comment="在系统跑步的次数")
    RunDate = db.Column(db.DateTime, comment="最后执行跑步的日期")
    Time = db.Column(db.DateTime, default=datetime.now, nullable=False, comment="加入的时间")

    @property
    def json(self):
        return to_json(self, self.__class__)


# 未跑步列表
class NRunIMEICodes(db.Model):
    __tablename__ = 'NRunIMEICodes'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    IMEICode = db.Column(db.String(255), nullable=False, unique=True, comment="IMEICode")
    Email = db.Column(db.String(255), comment="收件箱")
    WxUid = db.Column(db.String(150), comment="微信消息推送用户id")
    User = db.Column(db.String(100), nullable=False, comment="代理账号")
    UserId = db.Column(db.Integer, nullable=False, comment="阳光跑userid")
    Name = db.Column(db.String(50), nullable=False, comment="姓名")
    VipLib = db.Column(db.String(50), nullable=False, comment="VIP类型")
    VipedDate = db.Column(db.DateTime, nullable=False, comment="vip到期时间")
    VipRunNum = db.Column(db.Integer, nullable=False, comment="vip剩余跑步次数")
    State = db.Column(db.Integer, nullable=False, default=1, comment="IMEICode状态，1有效")

    @property
    def json(self):
        return to_json(self, self.__class__)


# Vip类型
class VipLib(db.Model):
    __tablename__ = 'VipLib'
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    Name = db.Column(db.String(50), nullable=False, comment="vip类型名", default="vip类型名")

    @property
    def json(self):
        return to_json(self, self.__class__)


# vip用户列表
class VipUsers(db.Model):
    __tablename__ = 'VipUsers'
    __searchable__ = ["User", "Name", "School", "UserId", "VipLib"]
    __msearch_analyzer__ = ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    User = db.Column(db.String(50), comment="网站账号")
    Name = db.Column(db.String(255), nullable=False, comment="姓名")
    School = db.Column(db.String(255), nullable=False, comment="学校")
    UserId = db.Column(db.Integer, nullable=False, comment="阳光用户ID")
    VipLib = db.Column(db.String(255), nullable=False, comment="vip类型")
    VipedDate = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="vip到期日期")
    VipRunNum = db.Column(db.Integer, default=0, comment="vip跑步次数")
    JoinDate = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="加入vip日期")

    @property
    def json(self):
        return to_json(self, self.__class__)


# 卡密
class Kamis(db.Model):
    __tablename__ = 'Kamis'
    __searchable__ = ['Kami', 'KamiLib', 'UseUser', 'UseName', 'UseUserId', "SCUser"]
    __msearch_analyzer__ = ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    Kami = db.Column(db.String(200), nullable=False, comment="卡密内容")
    KamiLib = db.Column(db.String(50), nullable=False, comment="卡密类型")
    Day = db.Column(db.Integer, nullable=False, comment="卡密天数")
    Num = db.Column(db.Integer, nullable=False, comment="卡密跑步次数")
    UseUser = db.Column(db.String(60), comment="使用卡密的用户")
    UseName = db.Column(db.String(100), comment="使用卡密的阳光跑姓名")
    UseUserId = db.Column(db.Integer, comment="使用卡密的阳光跑userid")
    UseDate = db.Column(db.DateTime, comment="使用卡密的日期")
    SCUser = db.Column(db.String(50), nullable=False, comment="生成卡密的用户")
    SCDate = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="卡密的生成日期")
    State = db.Column(db.Integer, nullable=False, default=0, comment="卡密使用状态：0未被使用 1已被使用")

    @property
    def json(self):
        return to_json(self, self.__class__)


# 系统日志
class SystemLog(db.Model):
    __tablename__ = "SystemLog"
    __searchable__ = ["LogContent", "LogLib", "UserName", "Time"]
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    LogContent = db.Column(db.TEXT(200), nullable=False, comment="日志内容")
    LogLib = db.Column(db.String(50), nullable=False, comment="日志的类别")
    UserName = db.Column(db.String(100), nullable=False, comment="网站用户名")
    Time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="创建消息的时间")

    @property
    def json(self):
        return to_json(self, self.__class__)


# 工单
class Workorder(db.Model):
    __tablename__ = 'Workorder'
    __searchable__ = ["User", "UserId", "WorkContent"]
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True, unique=True)
    User = db.Column(db.String(100), nullable=False, comment="网站账号")
    AdminUser = db.Column(db.String(50), nullable=False, comment="上级用户名")
    UserId = db.Column(db.String(255), nullable=True, comment="工单阳光跑userid")
    WorkorderContent = db.Column(db.String(255), nullable=False, comment="工单内容")
    MsgList = db.Column(db.TEXT, nullable=False, default=str([]), comment="消息列表")
    State = db.Column(db.Integer, nullable=False, default=0,comment="工单状态,0待回复1已回复2关闭")
    Time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment="创建工单的时间")
    CheckStatus = db.Column(db.Integer, nullable=False, default=0, comment="工单查看状态：0未查看1已查看")

    @property
    def json(self):
        return to_json(self, self.__class__)

