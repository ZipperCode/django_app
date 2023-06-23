import datetime
import logging
from typing import List

from django.db.models import QuerySet

from util import utils, time_utils
from util.time_utils import convert_date, convert_time
from web_app.decorators.admin_decorator import log_func
from web_app.model.accounts import AccountId, AccountQr, LineUserAccountIdRecord, LineUserAccountQrRecord
from web_app.model.users import User, USER_ROLE_BUSINESS
from web_app.util import dispatch

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


def filter_field(query: QuerySet, body) -> QuerySet:
    logging.info("filter_field# body = %s", body)
    country = body.get("country")
    mark = body.get("mark")
    date_start = body.get('date_start')
    date_end = body.get('date_end')
    op_user_id = body.get("op_user_select")
    op_username = body.get('op_username')
    used = body.get('used')
    # 过滤使用状态
    if not utils.str_is_null(used):
        query = query.filter(used=utils.is_bool_val(used))
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


def search_account_id_page(body, start_row, end_row, user: User):
    query = filter_field(AccountId.objects, body)
    res = list(
        query.values(
            'id', 'account_id', 'country', 'age', 'work', 'money', 'mark', 'used',
            'op_user__username', 'create_time', 'update_time'
        )
    )[start_row: end_row]

    return list(res), query.count()


@log_func
def search_account_qr_page(body, start_row, end_row, user_id):
    query = filter_field(AccountQr.objects, body)
    res = list(
        query.values(
            'id', 'qr_content', 'qr_path', 'country', 'age', 'work', 'money', 'mark', 'used',
            'op_user__username', 'create_time', 'update_time'
        )
    )[start_row: end_row]

    return list(res), query.count()


def dispatcher_account_id():
    logging.info("lineAccountId#处理id数据分发")
    # 用户表id列表和长度
    u_ids, len_u_ids = dispatch.get_user_ids()
    logging.info("lineAccountId#查询到业务员数量为 = %s", len_u_ids)
    # AccountId表数据
    a_ids, len_ids = dispatch.get_account_list(AccountId.objects)
    logging.info("lineAccountId#查询到当天新增的数据量为 = %s", len_ids)
    div_num, mod_num = dispatch.get_dispatcher_num(len_ids, len_u_ids)
    logging.info("lineAccountId#id数量为 = %s, 用户数量为= %s", len_ids, len_u_ids)
    logging.info("lineAccountId#每个用户分配Id数量为 = %s, 剩余未分配的数量为= %s", div_num, mod_num)

    bat_aid_record_list: List[LineUserAccountIdRecord] = []

    def add_record(_u_id, _a_id):
        bat_aid_record_list.append(
            LineUserAccountIdRecord(
                user_id=_u_id,
                a_id=_a_id,
                used=False,
                create_time=time_utils.get_now_bj_time(),
                update_time=time_utils.get_now_bj_time()
            )
        )

    logging.info("lineAccountId#处理数据分发用户")
    dispatch.dispatcher_user(a_ids, u_ids, div_num, mod_num, add_record)
    logging.info("lineAccountId#开始处理AccountIdRecord数据批量插入")
    LineUserAccountIdRecord.objects.bulk_create(bat_aid_record_list)


def dispatcher_account_qr():
    logging.info("lineAccountQr#处理二维码数据分发")
    # 用户表id列表和长度
    u_ids, len_u_ids = dispatch.get_user_ids()
    logging.info("lineAccountQr#查询到业务员数量为 = %s", len_u_ids)
    # AccountId表数据
    data_ids, len_ids = dispatch.get_account_list(AccountQr.objects)
    logging.info("lineAccountQr#查询到当天新增的数据量为 = %s", len_ids)
    div_num, mod_num = dispatch.get_dispatcher_num(len_ids, len_u_ids)
    logging.info("lineAccountQr#二维码数量为 = %s, 用户数量为= %s", len_ids, len_u_ids)
    logging.info("lineAccountQr#个用户分配Id数量为 = %s, 剩余未分配的数量为= %s", div_num, mod_num)
    bat_aid_record_list: List[LineUserAccountQrRecord] = []

    def add_record(_u_id, _a_id):
        bat_aid_record_list.append(
            LineUserAccountQrRecord(
                user_id=_u_id,
                qr_id=_a_id,
                create_time=time_utils.get_now_bj_time(),
                update_time=time_utils.get_now_bj_time()
            )
        )

    logging.info("lineAccountQr#处理数据分发用户")
    dispatch.dispatcher_user(data_ids, u_ids, div_num, mod_num, add_record)
    logging.info("lineAccountQr#开始处理 二维码-用户-记录 数据批量插入")
    LineUserAccountIdRecord.objects.bulk_create(bat_aid_record_list)
