# -*- coding: utf-8 -*-
"""
@Time    : 2022/12/12 9:30
@Author  : ghwg
@File    : WebClass.py
网站配置类
"""
from datetime import datetime

from module.mysql import WebConfig
from module.mysql.modus import get_sql_info, put_sql_info


class WebClass:
    # 获取网站配置
    @classmethod
    def get_web_config(cls):
        sql_data = get_sql_info(WebConfig)
        return sql_data

    # 修改网站配置
    @classmethod
    def put_web_info(cls, WebInfo: dict) -> dict:
        """
        :param WebInfo: 包含网站配置信息的字典
        :return: 修改网站配置结果字典
        """
        """获取数据库配置"""
        _sql = WebConfig.query.get(1)
        if _sql:
            """判断公告是否发生改变"""
            if _sql.WebGG == WebInfo['WebGG']:  # 公告未改变
                pass
            else:  # 公告发生改变 -> 更新公告时间
                WebInfo["PutDate"] = datetime.now()
            """修改数据库配置"""
            if put_sql_info(WebConfig, WebInfo):  # 配置修改成功
                return {"code": 200, "msg": "网站配置修改成功"}
            else:
                return {"code": 400, "msg": "配置修改失败,erro:配置数据获取失败"}
        else:
            return {"code": 400, "msg": "配置修改失败,erro:配置数据获取失败"}


"""实例化"""
web_class = WebClass()
