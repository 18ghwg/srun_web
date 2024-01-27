# -*- coding: utf-8 -*-
"""
@Time    : 2022/10/24 11:51
@Author  : ghwg
@File    : modus.py
通用的数据库操作方法
"""
import json

import sqlalchemy
from typing import Union

from sqlalchemy.orm.attributes import InstrumentedAttribute

from exts import app, db


# 获取数据库配置
def get_sql_info(tablename: db.Model) -> dict:
    """
    :param tablename: 数据库表名
    :return: 字典
    """
    sql_data = tablename.query.get(1)
    if sql_data:
        return sql_data.json
    else:
        return {}


# 修改数据库配置
def put_sql_info(tablename: db.Model, dic: dict) -> bool:
    """
    :param tablename: 数据表模型
    :param dic: 包含组名key和value的字典
    :return:
    """
    _data = tablename.query.filter_by(id=1)
    if _data:
        _data.update(dic)
        with app.app_context():
            db.session.commit()
        return True
    else:
        return False


# 处理数据库信息
def _mod(lis: sqlalchemy.engine.result.RowProxy) -> dict:
    """
    :param lis: 一组数据
    :return: 含有数据库所有信息的字典
    """
    keys = lis.keys()
    values = lis.values()
    _sql_data = {}  # 列表内的字典
    for index, key in enumerate(keys):
        _sql_data[key] = values[index]
    return _sql_data


# 获取数据库列表
def get_sql_list(tablename: db.Model, element: InstrumentedAttribute, *order_by: bool) -> list:
    """
    :param tablename: 类名
    :param element: 类元素
    :param order_by: 正序留空或倒序True
    :return: 返回一个数据表中全部的数据
    """
    # 操作数据库
    _data = tablename.query.order_by(element.desc() if order_by else None).all()
    if _data:
        # 获取表单数据
        sql_list = [sql.json for sql in _data]
        return sql_list
    else:
        return []



def search_sql_info(tablename: db.Model, info: list) -> list or None:
    """
    :param tablename: 表名
    :param info: 检索的列表[{"attribute": "健名1", "value": "键值1", "order_by": "排序列名", "sort_order": "asc或者desc"}]
    :return: 在指定的数据表中搜索数据并返回搜索结果的字典：[,,,]; 没有结果返回None
    """
    sql_data = tablename.query.filter_by().first()
    if sql_data:
        try:
            """
            构造sql语句
            多个条件检索
            """
            if len(info) > 1:
                sql_text = f"SELECT * FROM {sql_data.__tablename__} WHERE "
                for key in info:
                    sql_text += f"{key['attribute']} = '{key['value']}' AND "
                sql_text = sql_text.rstrip('AND ')  # 去除末尾的AND

                # 添加排序功能
                order_by = None
                sort_order = 'asc'
                for key in info:
                    if 'order_by' in key:
                        order_by = key['order_by']
                    if 'sort_order' in key:
                        sort_order = key['sort_order'].lower()

                if order_by:
                    sql_text += f" ORDER BY {order_by} {sort_order}"
            else:
                sql_text = f"SELECT * FROM {sql_data.__tablename__} WHERE {info[0]['attribute']} = '{info[0]['value']}'"

                # 添加排序功能
                order_by = None
                sort_order = 'asc'
                if 'order_by' in info[0]:
                    order_by = info[0]['order_by']
                if 'sort_order' in info[0]:
                    sort_order = info[0]['sort_order'].lower()

                if order_by:
                    sql_text += f" ORDER BY {order_by} {sort_order}"

            _data = db.session.execute(sql_text).fetchall()
        except IndexError:
            return None
        else:
            return [_mod(sql) for sql in _data]
    else:
        return None


# 全局模糊搜索返回json格式
def global_search_info(table_name: db.Model, key: Union[str, int], **info: dict) -> list:
    """
    :param table_name: 数据库模型名称
    :param key: 搜索关键词
    :param info: {"UserName": "", "Key": "", "userLib": "身份"}
                                    UserName: 用户名；Key：用户在模型中的身份名比如：UserLib：用户的身份；User、AdminAgent
    :return: 包含json格式搜索结果的list
    """

    if info:  # 进行角色筛选
        if info["UserLib"] == "管理员":  # 是管理员
            search_data = table_name.query.msearch(key).all()
            if search_data:
                return [data.json for data in search_data]
            else:
                return []
        else:
            search_all = table_name.query.msearch(key).all()  # 获取关于这个关键词全部的列表
            if search_all:
                search_all = [data.json for data in search_all]
                del_list = []
                """筛选出属于当前用户的数据"""
                for search_data in search_all:  # 找出不属于用户的数据并添加到待删除列表中
                    if search_data[info["Key"]] != info["UserName"]:  # 不是当前用户的数据
                        """加入删除列表"""
                        del_list.append(search_data)
                for del_data in del_list:  # 遍历待删除列表并删除数据
                    """开始删除"""
                    search_all.remove(del_data)
                return search_all
            else:
                return []

    else:  # 直接查询数据
        search_data = table_name.query.msearch(key).all()
        if search_data:
            """处理列表数据"""
            return [data.json for data in search_data]
        else:
            return []


"""

data = SystemLog.query.order_by(SystemLog.Time.desc()).all()
    print(data)
    info = []
    for data_info in data:
        info.append(data_info.json)
    return info

"""
