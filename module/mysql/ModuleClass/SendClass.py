# -*- coding: utf-8 -*-
"""
@Time    : 2022/11/5 22:38
@Author  : ghwg
@File    : SendClass.py

"""
from config import logger
from exts import app, db
from module.mysql import WebConfig


class SendClass:
    # 获取access_token
    @classmethod
    def get_access_token(cls, ):
        with app.app_context():
            get_token_data = WebConfig.query.get(1)
            return get_token_data.AccessToken

    # 更新access_token
    @classmethod
    def put_access_token(cls, token: str):
        with app.app_context():
            put_data = WebConfig.query.get(1)
            put_data.AccessToken = token
            db.session.commit()  # 提交更新
            logger.info("access token已更新！")


send_class = SendClass()
