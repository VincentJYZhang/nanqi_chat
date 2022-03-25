import time

def get_cur_time_string():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
