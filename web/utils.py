import os.path
import time


def log(*args, **kwargs):
    # time.time() 返回 unix time
    format = '%H:%M:%S'
    value = time.localtime(int(time.time()))
    dt = time.strftime(format, value)
    print(dt, *args, **kwargs)
    with open('gua.log.txt', 'a', encoding='utf-8') as f:
        print(dt, *args, file=f, **kwargs)


def formatted_time(int_time):
    """
    把int类型时间格式化
    """
    t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int_time))
    return t