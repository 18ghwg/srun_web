from datetime import timedelta
import ssl
from log import Logger

from tempfile import mkdtemp

# logging
logger = Logger().logger

# 数据库
HOSTNAME = '124.222.113.243'
PORT = '3306'
DATABASE = 'srun_new'
USERNAME = 'srun_new'
PASSWORD = 'rAAMzmMb68BjXWe5'
# DATABASE = 'srun_ceshi'
# USERNAME = 'srun_ceshi'
# PASSWORD = 'DYGhCbR7iCDJKJaf'
DB_URI = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = True
SQLALCHEMY_DATABASE_URI = DB_URI
MSEARCH_INDEX_NAME = mkdtemp()
MSEARCH_PRIMARY_KEY = 'id'
MSEARCH_ENABLE = True

# 全局取消证书验证
ssl._create_default_https_context = ssl._create_unverified_context

# session密钥
SECRET_KEY = "KJKLEREKRkeljrljeklsjrkflsFKL"  # session密钥
PERMANENT_SESSION_LIFETIME = timedelta(days=2)  # 设置cookie为7天过期

# redis缓存配置
CACHE_DEFAULT_TIMEOUT = 60
CACHE_REDIS_HOST = 'localhost'
CACHE_REDIS_PORT = 6379
CACHE_REDIS_PASSWORD = "Sun0218"
CACHE_TYPE = 'redis'

#  路由配置-生产环境下部署请开启
# SESSION_COOKIE_DOMAIN = 'srun.vip'
# SERVER_NAME = 'srun.vip'

# 本机测试需打开
# 并修改C:\Windows\System32\drivers\etc/hosts文件，在文件中添加 127.0.0.1  srun.vip 等二级域名
# SERVER_NAME = 'srun.vip:5100'

# 禁用静态文件缓存
# SEND_FILE_MAX_AGE_DEFAULT = 0


