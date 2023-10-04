import logging

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
        query = query.filter(account__used=utils.get_status(used))
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


def search_account_common_field(query: QuerySet, body) -> QuerySet:
    logging.info("search_account_common_field# body = %s", body)
    country = body.get("country")
    mark = body.get("mark")
    date_start = body.get('date_start')
    date_end = body.get('date_end')
    op_user_id = body.get("op_user_select")
    op_username = body.get('op_username')
    used = body.get('used')
    query.filter(op_user__isnull=False)
    # 过滤使用状态
    if not utils.str_is_null(used):
        query = query.filter(used=utils.get_status(used))
    # 模糊搜索上传人
    if not utils.str_is_null(op_username):
        query = query.filter(op_user__username__contains=op_username)
    if utils.is_int(op_user_id):
        query = query.filter(op_user_id=op_user_id)
    # 模糊搜索城市
    if not utils.str_is_null(country):
        query = query.filter(country__contains=country)
    # 模糊搜索备注
    if not utils.str_is_null(mark):
        query = query.filter(mark__contains=country)
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
