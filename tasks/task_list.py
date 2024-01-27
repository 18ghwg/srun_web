# flask 定时任务的方法
import hashlib


class Config(object):
    JOBS = [  # 任务列表
        {
            'id': '阳光体育now',
            'func': 'tasks:run_now',
            'trigger': 'cron',  # 定时方法
            'day': '*',  # 每天
            'hour': '*',
            'minute': '*',
        },
        {
            'id': '阳光体育all',
            'func': 'tasks:run_all',
            'trigger': 'date',  # 定时方法
            'run_date': '2099-7-25 19:42:50'
        },
        {
            'id': '跑步情况每日推送',
            'func': 'tasks:send_run_info',
            'trigger': 'cron',  # 定时方法
            'day': '*',  # 每天
            'hour': '23',
            'minute': '00',
        },
        {
            'id': '检测今日未跑步的用户并补偿vip',
            'func': 'tasks:check_today_nrun_imei',
            'trigger': 'cron',  # 定时方法
            'day': '*',  # 每天
            'hour': '23',
            'minute': '30',
        },
        {
            'id': '检测前几分钟未跑步的账号并加入未跑步列表中',
            'func': 'tasks:check_now_nrun_imei',
            'trigger': 'cron',  # 定时方法
            'day': '*',  # 每天
            'hour': '*',
            'minute': '*',  # 每分钟
        },
        {
            'id': '清理用户系统操作日志',
            'func': 'tasks:clear_system_log',
            'trigger': 'cron',  # 定时方法
            'day': '*',  # 每天
            'hour': '*',
            'minute': '*/2',
        },
    ]

    SCHEDULER_API_ENABLED = True  # 开启API
    key = hashlib.md5(b'ghwg').hexdigest()
    _key = key[:5] + 'ghwg' + key[5:]
    # print(_key)
    SCHEDULER_API_PREFIX = f'/{_key}'  # api前缀
    SCHEDULER_TIMEZONE = 'Asia/Shanghai'  # 设置时区
    SCHEDULER_MAX_INSTANCES = 15  # 最大实例数



