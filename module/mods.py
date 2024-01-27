# -*- coding: utf-8 -*-
"""
@Time    : 2022/10/23 18:17
@Author  : ghwg
@File    : mods.py

"""
# 处理post信息
import re
from urllib.parse import unquote

from flask import request

from config import logger
from module.send import sendwxbot


# 检测邮箱格式
def check_email(email: str):
    if email:
        if '@qq.com' in email:
            try:
                int(email.split('@')[0])
            except ValueError:
                return False
            else:
                return True
        else:
            return False
    else:
        return False


# 处理跑步时间
def mod_run_time(RunTime: str):
    _runtime = RunTime.split(':')  # 列表化跑步时间
    if len(_runtime) == 3:  # 用户选择了秒
        RunTime = _runtime[0] + ':' + _runtime[1]
    else:
        RunTime = RunTime
    return RunTime


# 异常捕获钩子函数
def log_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"异常捕获到函数：{func.__name__}报错: {e}")
            sendwxbot(f"异常捕获到函数：{func.__name__}报错: {e}")
            raise
    return wrapper


# 判断字符串是否是纯英文
def is_english(text):
    """
    :param text:字符串
    :return: True：纯英文；False：非纯英文
    """
    pattern = r'^[a-zA-Z]+$'
    return bool(re.match(pattern, text))


# 判断字符串中是否有标点符号
def has_punctuation(text):
    """
    :param text: 任意字符串
    :return: True：字符砖含有特殊符号或者含有空格；反之：False
    """
    pattern = r'[^\w\s]'
    if re.search(pattern, text):
        return True  # 字符串中包含特殊字符
    elif ' ' in text:
        return True  # 字符串中包含空格
    else:
        return False  # 字符串中既没有特殊字符也没有空格


def has_chinese(text):
    """
    :param text:字符串
    :return: True：含有中文；False；无中文
    """
    pattern = re.compile(r'[\u4e00-\u9fff]')
    if re.search(pattern, text):
        return True  # 字符串中包含中文字符
    else:
        return False  # 字符串中不包含中文字符
