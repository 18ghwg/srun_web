# -*- coding: utf-8 -*-
"""
@Time    : 2022/11/5 22:34
@Author  : ghwg
@File    : EmailClass.py

"""
import random
from datetime import datetime

from config import logger
from exts import db
from module.mysql import Register, Users, ResetPassword
from module.mysql.ModuleClass.WebClass import web_class
from module.send import send_email


class EmailClass:
    # 获取验证码
    @classmethod
    def send_emailcode(cls, email: str):
        """
        :param email: 邮箱
        :return: dict
        """
        send_max = web_class.get_web_config()["SendEmailMaxNum"]  # 发送邮件的最大次数
        mail_code = random.randint(1111, 9999)  # 生成随机验证码
        _data = Register.query.filter_by(Email=email).first()
        if _data:  # 已存在
            if _data.SendNum <= send_max:  # 没超过验证次数
                # 更新信息
                _data.SendNum += 1  # 验证次数加一
                _data.Code = mail_code
                _data.Time = datetime.now()
                db.session.commit()
                # 发送邮件
                send_email(email, f'你的注册验证码是：{mail_code}', "注册验证码")
                logger.info(f"{email}验证码已发送")
                return {"code": 200, "msg": f"验证码已发送, 你还有{send_max - _data.SendNum if _data.SendNum < 5 else 0}次发送机会。"
                                            f"<br>收不到邮件请添加blog18.cn为QQ邮箱域名白名单"}
            else:
                return {"code": 400, "msg": "发送失败, 该邮箱超过验证最大次数"}
        else:  # 不存在->新增
            add_data = Register(Email=email, Code=mail_code)
            db.session.add(add_data)
            db.session.commit()
            # 发送邮件
            send_email(email, f'你的注册验证码是：{mail_code}', "注册验证码")
            logger.info("验证码已发送到你的邮箱")
            return {"code": 200, "msg": "验证码已发送到你的邮箱."}

    # 删除用户注册验证信息
    @classmethod
    def del_register_info(cls, email: str):
        """
        :param email: 要删除的邮箱信息
        :return: 无
        """
        Register.query.filter_by(Email=email).delete()
        db.session.commit()

    # 发送密码重置邮件
    @classmethod
    def send_reset_password_email(cls, email: str):
        """
        :param email: 用户的邮箱
        :return: 发送重置密码邮件的状态
        """
        """搜索用户数据 -> 判断邮箱是否存在"""
        email_data = Users.query.filter_by(Email=email).first()
        if email_data:  # 搜到了
            """获取用户信息"""
            UserName = email_data.UserName  # 用户名
            """生成重置密钥信息"""
            base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
            length = len(base_str) - 1
            token = ''
            for i in range(20):
                token += base_str[random.randint(0, length)]
            """上传密码重置信息"""
            re_data = ResetPassword.query.filter_by(Email=email).first()
            if re_data:  # 信息已存在 -> 更新信息
                re_data.Token = token
                re_data.UserName = UserName
                re_data.Time = datetime.now()
                db.session.commit()  # 提交数据
            else:  # 信息不存在 -> 新建密码重置信息
                add_data = ResetPassword(
                    UserName=UserName,
                    Email=email,
                    Token=token,
                )
                db.session.add(add_data)
                db.session.commit()  # 提交数据新增
            """发送邮件"""
            """获取网站配置"""
            web_config = web_class.get_web_config()
            web_name = web_config['WebName']  # 网站名称
            web_url = web_config['WebUrl']  # 网站链接
            send_email(
                email,
                f'您收到此邮件是因为您在{web_name}网站申请了密码重置,如果不是您申请的,请忽略此邮件.<br>若要开始重置密码,请点击以下链接 :)'
                '<td align="center"><table cellspacing="0" cellpadding="0" border="0" class="bmeButton" '
                'align="center" style="border-collapse: separate;"><tbody><tr><td style="border-radius: 5px; '
                'border-width: 0px; border-style: none; border-color: transparent; background-color: rgb(112, '
                '97, 234); text-align: center; font-family: Arial, Helvetica, sans-serif; font-size: 18px; '
                'padding: 15px 30px; font-weight: bold; word-break: break-word;" class="bmeButtonText"><span '
                'style="font-family: Helvetica, Arial, sans-serif; font-size: 18px; color: rgb(255, 255, '
                '255);"><a style="color: rgb(255, 255, 255); text-decoration: none;" target="_blank" '
                f'draggable="false" href="{web_url}/user/password/token/{token}" data-link-type="web" '
                f'rel="noopener">点此链接进入密码重置'
                '</a></span></td></tr></tbody></table>',
                f"{web_name}重置密码"
            )
            return {"code": 200, "msg": "重置密码的邮件已发送到你的邮箱!"}
        else:  # 邮箱不存在
            return {"code": 1, "msg": "你输入的邮箱并没有注册过呀~"}


email_class = EmailClass()
