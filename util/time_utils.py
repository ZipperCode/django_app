import logging
from datetime import timezone, timedelta, datetime
from typing import Optional

import pytz
from pytz import UTC

from util import utils

TIME_ZONE_ASIA_SHANG_HAI = timezone(
    timedelta(hours=8),
    name='Asia/Shanghai',
)

TIME_ZONE_AUSTRALIA_SYDNEY = timezone(
    timedelta(hours=10),
    name='Australia/Sydney',
)

DATE_FORMAT = "%Y-%m-%d"
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"


def get_now_bj_time() -> datetime:
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    return utc_now.astimezone(TIME_ZONE_ASIA_SHANG_HAI)


def get_now_sydney_time() -> datetime:
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    return utc_now.astimezone(TIME_ZONE_AUSTRALIA_SYDNEY)
    # return datetime.now(tz=UTC)


def fmt_utc2sydney_time(t):
    if t is None:
        return ""
    try:
        if isinstance(t, str):
            t = datetime.strptime(t, DATE_TIME_FORMAT)
        if isinstance(t, datetime):
            return datetime.astimezone(TIME_ZONE_AUSTRALIA_SYDNEY).strftime(DATE_TIME_FORMAT)
    except BaseException as e:
        logging.exception(e)
        pass
    return t


def convert_date(t_str: str) -> Optional[datetime]:
    return convert_time(t_str, DATE_FORMAT)


def convert_time(t_str: str, fmt: str = DATE_TIME_FORMAT) -> Optional[datetime]:
    if utils.str_is_null(t_str):
        return None
    try:
        return datetime.strptime(t_str, fmt)
    except BaseException as e:
        logging.exception(e)
        pass
    return None


def get_utc_time() -> datetime:
    utc_tz = pytz.timezone('UTC')
    return datetime.now(tz=utc_tz)


def fmt_datetime(t: datetime, fmt: Optional[str] = DATE_TIME_FORMAT):
    if fmt is None:
        return t.strftime(DATE_TIME_FORMAT)
    return t.strftime(fmt)


def get_ymd_tuple(cur_time: datetime):
    cur_year = cur_time.year
    cur_month = cur_time.month
    cur_day = cur_time.day
    return cur_year, cur_month, cur_day


def convert_timezone(time_in):
    """
    用来将系统自动生成的datetime格式的utc时区时间转化为本地时间
    :param time_in: datetime.datetime格式的utc时间
    :return:输出仍旧是datetime.datetime格式，但已经转换为本地时间
    """
    time_utc = time_in.replace(tzinfo=pytz.timezone('UTC'))
    time_local = time_utc.astimezone(pytz.timezone('Asia/Shanghai'))
    return time_local


def convert_local_timezone(time_in):
    """
    用来将输入的datetime格式的本地时间转化为utc时区时间
    :param time_in: datetime.datetime格式的本地时间
    :return:输出仍旧是datetime.datetime格式，但已经转换为utc时间
    """
    local = pytz.timezone('Asia/Shanghai')
    local_dt = local.localize(time_in, is_dst=None)
    time_utc = local_dt.astimezone(pytz.utc)
    return time_utc


def get_now_utc():
    return datetime.utcnow()


if __name__ == '__main__':
    print(get_now_sydney_time())
    print(get_now_bj_time())
    pass
