import os

from flask import Flask, request
from flask_limiter import Limiter
from flask_sqlalchemy import SQLAlchemy
from flask_msearch import Search
from flask_wtf import CSRFProtect
import redis

app = Flask(__name__, static_url_path='')

csrf = CSRFProtect()


# 限流器全局配置
def limit_key_func():
    return str(request.headers.get("X-Forwarded-For", '127.0.0.1'))


limiter = Limiter(
    app, key_func=limit_key_func,
    default_limits=["20 per minute"],
    storage_uri="redis://default:123456@127.0.0.1:6379",
)

db = SQLAlchemy()

# 全局搜索器
search = Search(app, db=db)

# redis链接配置
redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, password="123456", db=0)  # 连接 Redis

# 系统根目录
root_dir = os.path.dirname(os.path.abspath(__file__))


