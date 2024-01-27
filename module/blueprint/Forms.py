# -*- coding: utf-8 -*-
"""
@Time    : 2023/3/8 15:47
@Author  : ghwg
@File    : Forms.py

"""
import re
import string

import wtforms
from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms.validators import Email, Length, EqualTo, DataRequired, ValidationError, Optional

from exts import db
from module.mods import check_email
from module.mysql import Users, Register, WebConfig


# 检测是否含有中文
def validate_chinese(form, field):
    if field.data:
        if re.search(r'[\u4e00-\u9fa5]', field.data):
            raise ValidationError(message=f"{field.label.text}中不能包含中文")


# QQ数字邮箱检测
def validate_email(form, field):
    if field.data:
        if not check_email(field.data):
            raise ValidationError(message=f"邮箱应为QQ数字邮箱")


# IMEICode检测
def validate_imei(form, field):
    if field.data:
        if "=" in field.data:
            raise ValidationError(message="IMEICode是=后面的32位纯字符")


# 检测数据是否有符号
def has_punctuation(input_str):
    for char in input_str:
        if char in string.punctuation:
            return True
    return False


# 注册验证
class RegisterForm(FlaskForm):
    username = wtforms.StringField(label="用户名", validators=[DataRequired(message="用户名为空"),
                                                            Length(min=4, max=11, message="用户名长度应为4-11"),
                                                            validate_chinese], )  # 用户名
    password = wtforms.StringField(label="密码", validators=[DataRequired(message="密码为空"),
                                                           Length(min=6, max=15, message="密码长度应为6-15"),
                                                           EqualTo("password_confirmation", message="两次密码不一致"),
                                                           validate_chinese])  # 密码
    password_confirmation = wtforms.StringField(label="确认密码", validators=[DataRequired(message="确认密码为空"),
                                                                          Length(min=6, max=15),
                                                                          EqualTo("password", message="两次密码不一致"),
                                                                          validate_chinese])  # 确认密码
    email = wtforms.StringField(label="邮箱", validators=[DataRequired(message="邮箱为空"),
                                                        Email(message="邮箱格式错误"),
                                                        validate_chinese, validate_email])  # 邮箱
    qqh = wtforms.StringField(label="QQ号", validators=[DataRequired(message="QQ号为空"),
                                                       Length(min=6, max=11, message="QQ号格式错误"),
                                                       validate_chinese])  # QQ号
    code = wtforms.StringField(label="验证码", validators=[DataRequired(message="验证码为空"),
                                                        Length(min=4, max=4, message="验证码格式错误"),
                                                        validate_chinese])  # 验证码

    # 自定义验证
    # 验证邮箱
    def validate_email(self, field):
        email = field.data
        """是否被注册"""
        email_data = Users.query.filter_by(Email=email).first()
        if email_data:
            raise ValidationError(message="该邮箱已经被注册")

    # 验证验证码
    def validate_code(self, field):
        code = field.data
        email = self.email.data
        regist_data = Register.query.filter_by(Email=email, Code=code).first()
        if not regist_data:
            raise ValidationError(message="邮箱或验证码错误")
        else:
            # 删除注册信息
            db.session.delete(regist_data)
            db.session.commit()

    # 检查用户是否被注册了
    def validate_username(self, field):
        username = field.data
        """重复验证"""
        user_data = Users.query.filter_by(UserName=username).first()
        if user_data:
            raise ValidationError(message="用户名已存在")
        """符号验证"""
        if has_punctuation(username):
            raise ValidationError(message="用户名不能包含符号")


# 发送注册验证码
class SendEmailCode(FlaskForm):
    email = wtforms.StringField(label="邮箱", validators=[DataRequired(message="邮箱为空"),
                                                        Email(message="你的邮箱格式不正确"), validate_chinese, validate_email])

    # 自定义验证
    # 检查邮箱
    def validate_email(self, field):
        """获取信息"""
        email = field.data
        web_data = WebConfig.query.get(1)  # 获取网站配置
        send_max_num = web_data.SendEmailMaxNum  # 最大发送次数

        """检查邮箱是否被注册"""
        email_data = Users.query.filter_by(Email=email).first()
        if email_data:
            raise ValidationError(message="该邮箱已被注册")

        """是否发送次数上限"""
        email_data = Register.query.filter(Register.Email == email, Register.SendNum >= send_max_num).first()
        if email_data:
            raise ValidationError(message="邮箱超过最大发送次数")


# 添加代理检测
class AddAgent(FlaskForm):
    UserName = wtforms.StringField(label="代理用户名", validators=[DataRequired(message="用户名不得为空"),
                                                              Length(min=4, max=11, message="代理用户名长度应为4-11")])
    Password = wtforms.StringField(label="密码", validators=[DataRequired(message="密码不能为空"),
                                                           Length(min=6, max=15, message="密码长度应为6-15")])
    QQh = wtforms.StringField(label="QQ号", validators=[DataRequired(message="QQ号不能为空"),
                                                       Length(min=6, max=12, message="qq号的长度应为6-12")])
    Email = wtforms.StringField(label="邮箱", validators=[DataRequired(message="邮箱不能为空"),
                                                        Email(message="邮箱格式不正确"), validate_email])
    AdminUser = wtforms.StringField(label="上级用户名", validators=[Optional(True)])

    """自定义验证"""

    # 用户名
    def validate_UserName(self, field):
        UserName = field.data
        # 账号重复检测
        user_data = Users.query.filter(Users.UserName == func.binary(UserName)).first()
        if user_data:
            raise ValidationError(message="该用户已被注册")

    # 邮箱
    def validate_Email(self, field):
        Email = field.data
        email_data = Users.query.filter_by(Email=Email).first()
        if email_data:
            raise ValidationError(message="代理邮箱已被注册")


# 网站后台用户添加IMEICode检测
class UserAddIMEICode(FlaskForm):
    IMEICode = wtforms.StringField(
        label="IMEICode", validators=[DataRequired(message="IMEICode不能为空"),
                                      Length(min=32, max=32, message="IMEICode长度应为32位的纯字母字符"), validate_chinese, validate_imei])
    Email = wtforms.StringField(label="邮箱", validators=[Optional(True), Email(message="邮箱格式不正确"), validate_chinese, validate_email])
    run_time = wtforms.StringField(label="跑步时间", validators=[DataRequired(message="跑步时间不能为空"), validate_chinese])


# 重置密码检测
class RePassword(FlaskForm):
    password = wtforms.StringField(label="密码", validators=[Length(min=6, max=15, message="密码长度应为6-15"), validate_chinese])


# 新建工单检测器
class WorkorderAdd(FlaskForm):
    WorkorderContent = wtforms.StringField(label="工单内容", validators=[DataRequired(message="工单内容不能为空"),
                                                                         Length(max=200, message="内容长度不得超过200字")])

