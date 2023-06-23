from django.db.models import QuerySet

from util import utils
from util.time_utils import convert_time


def search_record_common(query: QuerySet, body) -> QuerySet:
    username = body.get('username')
    used = body.get('used')
    date_start = body.get('date_start')
    date_end = body.get('date_end')
    # 过滤使用状态
    if not utils.str_is_null(used):
        query = query.filter(account__used=utils.is_bool_val(used))
    # 模糊记录用户
    if not utils.str_is_null(username):
        query = query.filter(user__username__contains=username)
    # 开始结束时间
    if not utils.str_is_null(date_start):
        start = convert_time(date_start)
        if start is not None:
            query = query.filter(create_time__gte=start)
    if not utils.str_is_null(date_end):
        end = convert_time(date_end)
        if end is not None:
            query = query.filter(create_time__lt=end)

    return query
