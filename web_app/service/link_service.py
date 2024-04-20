import logging

import util.utils
from util import utils, time_utils
from web_app.model.link import AccountLink
from web_app.model.users import User
from web_app.util import rest_list_util
from web_app.model.const import UsedStatus
from util.exception import BusinessException


def query_list_page(body, start_row, end_row):
    logging.info("query_link_list_page# body = %s", body)
    date_start = body.get('date_start')
    date_end = body.get('date_end')
    op_username = body.get('op_username')
    op_user_id = body.get("op_user_select")
    mark = body.get("remark")
    link = body.get('link')
    query_args = {}

    if not utils.str_is_null(link):
        query_args['link__contains'] = link

    # 模糊搜索上传人
    if not utils.str_is_null(op_username):
        query_args['op_user__username__contains'] = op_username
    if utils.is_int(op_user_id):
        query_args['op_user__id'] = op_user_id

    # 模糊搜索备注
    if not utils.str_is_null(mark):
        query_args['remark__contains'] = mark
    # 开始结束时间
    if not utils.str_is_null(date_start):
        start = time_utils.convert_time(date_start)
        if start is not None:
            query_args['create_time__gte'] = start
    if not utils.str_is_null(date_end):
        end = time_utils.convert_time(date_end)
        if end is not None:
            query_args['create_time__lt'] = end

    query = AccountLink.objects
    if len(query_args) > 0:
        query = query.filter(**query_args)
    query_result = query.values(
        'id', 'link', 'remark', 'op_user__username', 'create_time', 'update_time'
    ).order_by('create_time')[start_row: end_row]

    return list(query_result), query.count()


def insert(body, user):
    link = body.get("link")
    remark = body.get("remark")

    if utils.str_is_null(link):
        raise BusinessException.msg("链接不能为空")

    if len(link) < 15:
        raise BusinessException("链接长度不能小于15")

    exists = AccountLink.objects.filter(link=link).exists()
    if exists:
        raise BusinessException("记录已存在")

    AccountLink.objects.create(
        link=link,
        remark=remark,
        op_user_id=user.id,
        used=UsedStatus.Default,
        create_time=time_utils.get_now_utc(),
        update_time=time_utils.get_now_utc()
    )


def update(body, user):
    link_id = body.get("id")
    link = body.get("link")
    remark = body.get("remark")
    exists = AccountLink.objects.filter(id=link_id).exists()
    if not exists:
        raise BusinessException("记录不存在")

    if utils.str_is_null(link):
        raise BusinessException("链接不能为空")

    AccountLink.objects.filter(id=link_id).update(
        link=link,
        remark=remark,
        update_time=time_utils.get_now_utc()
    )


def delete(body):
    link_id = body.get("id")
    AccountLink.objects.filter(id=link_id).delete()
