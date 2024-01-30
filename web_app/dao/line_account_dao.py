import logging
from typing import List, Tuple, Dict

from django.db import transaction
from django.db.models import F

from util import utils, time_utils
from web_app.decorators.admin_decorator import log_func
from web_app.model.accounts import AccountId, AccountQr, LineUserAccountIdRecord, LineUserAccountQrRecord
from web_app.model.const import UsedStatus
from web_app.model.users import User, USER_ROLE_UPLOADER, UserAccountRecord, RECORD_TYPE_LINE_ID, \
    RECORD_TYPE_LINE_QR, USER_BACK_TYPE_LINE
from web_app.util import dispatch, rest_list_util

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


def search_account_id_page(body, start_row, end_row, user: User):
    query = rest_list_util.search_account_common_field(AccountId.objects, body)
    account_id = body.get("account_id")
    if not utils.str_is_null(account_id):
        query = query.filter(account_id__contains=account_id)
    if user.role == USER_ROLE_UPLOADER:
        logging.info("当前用户是角色是上传人，取上传的数据")
        query = query.filter(used=UsedStatus.Default, op_user__id=user.id)

    res = list(
        query.values(
            'id', 'account_id', 'country', 'age', 'work', 'money', 'mark', 'used', 'is_bind',
            'op_user__username', 'create_time', 'update_time'
        ).order_by('create_time')[start_row: end_row]
    )

    return list(res), query.count()


@log_func
def search_account_qr_page(body, start_row, end_row, user: User):
    query = rest_list_util.search_account_common_field(AccountQr.objects, body)
    qr_content = body.get("qr_content")
    if not utils.str_is_null(qr_content):
        query = query.filter(qr_content__contains=qr_content)
    if user.role == USER_ROLE_UPLOADER:
        logging.info("当前用户是角色是上传人，取上传的数据")
        query = query.filter(used=UsedStatus.Default, op_user__id=user.id)

    res = list(
        query.values(
            'id', 'qr_content', 'qr_path', 'country', 'age', 'work', 'money', 'mark', 'used', 'is_bind',
            'op_user__username', 'create_time', 'update_time'
        ).order_by('create_time')[start_row: end_row]
    )

    return list(res), query.count()


def dispatcher_account_id(is_all: bool = False) -> Tuple[int, str]:
    logging.info("lineAccountId#处理id数据分发")
    # 用户表id列表和长度
    u_ids, len_u_ids = dispatch.get_business_user_ids2(USER_BACK_TYPE_LINE)
    logging.info("lineAccountId#查询到业务员数量为 = %s", len_u_ids)
    if len_u_ids == 0:
        return -1, "未找到可用的业务员"
    # AccountId表数据
    a_ids, len_ids = dispatch.get_account_list(AccountId.objects, is_all)
    if len_ids == 0:
        return -1, "未找到当日可分配的数据"
    logging.info("lineAccountId#查询到当天新增的数据量为 = %s", len_ids)
    div_num, mod_num = dispatch.get_dispatcher_num(len_ids, len_u_ids)
    logging.info("lineAccountId#id数量为 = %s, 用户数量为= %s", len_ids, len_u_ids)
    logging.info("lineAccountId#每个用户分配Id数量为 = %s, 剩余未分配的数量为= %s", div_num, mod_num)

    bat_aid_record_list: List[LineUserAccountIdRecord] = []

    u_record_map, max_num = dispatch.user_num_record2(LineUserAccountIdRecord.objects, u_ids, RECORD_TYPE_LINE_ID)
    add_u_ids = set()
    add_a_ids = set()

    def add_record(_u_id, _a_id):
        _num = u_record_map.get(_u_id)
        if _num is None:
            _num = 1
        else:
            _num += 1
        add_u_ids.add(_u_id)
        u_record_map[_u_id] = _num
        add_a_ids.add(_a_id)
        bat_aid_record_list.append(
            LineUserAccountIdRecord(
                user_id=_u_id,
                account_id=_a_id,
                used=UsedStatus.Default,
                create_time=time_utils.get_now_bj_time_str(),
                update_time=time_utils.get_now_bj_time_str()
            )
        )

    logging.info("lineAccountId#处理数据分发用户")
    # dispatch.dispatcher_user(a_ids, u_ids, div_num, mod_num, add_record)
    dispatch.dispatcher_user2(a_ids, u_ids, u_record_map.copy(), max_num, add_record)
    logging.info("lineAccountId#开始处理AccountIdRecord数据批量插入")

    if len(bat_aid_record_list) == 0:
        return -1, "分配失败，原因:len = 0"

    with transaction.atomic():
        logging.info("lineAccountId#开始数据库事务")
        logging.info("lineAccountId#插入Id记录信息")
        # 插入记录信息
        LineUserAccountIdRecord.objects.bulk_create(bat_aid_record_list)
        logging.info("lineAccountId#开始处理用户当天数据数量")
        dispatch.handle_user_record(u_record_map, RECORD_TYPE_LINE_ID)
        logging.info("lineAccountId#将数据 bind 设置为True ids = %s", add_a_ids)
        AccountId.objects.filter(id__in=add_a_ids).update(is_bind=True)

    return 0, f"成功分配{len_ids}条数据到{len(add_u_ids)}个业务员手中"


def dispatcher_account_qr(is_all: bool) -> Tuple[int, str]:
    logging.info("lineAccountQr#处理二维码数据分发")
    # 用户表id列表和长度
    u_ids, len_u_ids = dispatch.get_business_user_ids2(USER_BACK_TYPE_LINE)
    logging.info("lineAccountQr#查询到业务员数量为 = %s", len_u_ids)
    if len_u_ids == 0:
        return -1, "未找到可用的业务员"
    # AccountId表数据
    data_ids, len_ids = dispatch.get_account_list(AccountQr.objects, is_all)
    if len_ids == 0:
        return -1, "未找到当日可分配的数据"
    logging.info("lineAccountQr#查询到当天新增的数据量为 = %s", len_ids)
    logging.info("lineAccountQr#二维码数量为 = %s, 用户数量为= %s", len_ids, len_u_ids)
    bat_aid_record_list: List[LineUserAccountQrRecord] = []

    u_record_map, max_num = dispatch.user_num_record2(LineUserAccountQrRecord.objects, u_ids, RECORD_TYPE_LINE_QR)
    add_u_ids = set()
    add_a_ids = set()

    def add_record(_u_id, _a_id):
        logging.info("add_record = uid = %s, id = %s", _u_id, _a_id)
        _num = u_record_map.get(_u_id)
        if _num is None:
            _num = 1
        else:
            _num += 1
        u_record_map[_u_id] = _num
        add_u_ids.add(_u_id)
        add_a_ids.add(_a_id)
        bat_aid_record_list.append(
            LineUserAccountQrRecord(
                user_id=_u_id,
                account_id=_a_id,
                create_time=time_utils.get_now_bj_time_str(),
                update_time=time_utils.get_now_bj_time_str()
            )
        )

    logging.info("lineAccountQr#处理数据分发用户")
    # dispatch.dispatcher_user(data_ids, u_ids, div_num, mod_num, u_record_map, add_record)
    dispatch.dispatcher_user2(data_ids, u_ids, u_record_map.copy(), max_num, add_record)
    if len(bat_aid_record_list) == 0:
        return -1, "分配失败，原因:len = 0"
    logging.info("lineAccountQr#开始处理 二维码-用户-记录 数据批量插入")
    with transaction.atomic():
        logging.info("lineAccountQr#开始数据库事务")
        logging.info("lineAccountQr#插入Id记录信息")
        LineUserAccountQrRecord.objects.bulk_create(bat_aid_record_list)
        logging.info("lineAccountQr#开始处理用户当天数据数量")
        dispatch.handle_user_record(u_record_map, RECORD_TYPE_LINE_QR)
        logging.info("lineAccountQr#将数据 bind 设置为True")
        AccountQr.objects.filter(id__in=add_a_ids).update(is_bind=True)

    return 0, f"成功分配{len_ids}条数据到{len(add_u_ids)}个业务员手中"
