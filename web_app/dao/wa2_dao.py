import logging
import warnings
from typing import List, Tuple

from django.db import transaction

from util import utils, time_utils
from web_app.decorators.admin_decorator import log_func
from web_app.model.const import UsedStatus
from web_app.model.users import User, USER_ROLE_UPLOADER, RECORD_TYPE_WA_ID2, \
    RECORD_TYPE_WA_QR2, USER_BACK_TYPE_WA2
from web_app.model.wa_accounts2 import WaAccountId2, WaAccountQr2, WaUserIdRecord2, WaUserQrRecord2
from web_app.util import dispatch, rest_list_util

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


def search_account_id_page(body, start_row, end_row, user: User):
    warnings.warn("deprecated", DeprecationWarning)
    query = rest_list_util.search_account_common_field(WaAccountId2.objects, body)
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
    warnings.warn("deprecated", DeprecationWarning)
    query = rest_list_util.search_account_common_field(WaAccountQr2.objects, body)
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
    warnings.warn("deprecated", DeprecationWarning)
    logging.info("WaAccountId2#处理id数据分发")
    # 用户表id列表和长度
    u_ids, len_u_ids = dispatch.get_business_user_ids2(USER_BACK_TYPE_WA2)
    logging.info("WaAccountId2#查询到业务员数量为 = %s", len_u_ids)
    if len_u_ids == 0:
        return -1, "未找到可用的业务员"
    # AccountId表数据
    a_ids, len_ids = dispatch.get_account_list(WaAccountId2.objects, is_all)
    logging.info("a_ids= %s, len = %s", a_ids, len_ids)
    if len_ids == 0:
        if is_all:
            return -1, "未找到可分配的数据"
        return -1, "未找到当日可分配的数据"
    logging.info("WaAccountId2#查询到当天新增的数据量为 = %s", len_ids)
    div_num, mod_num = dispatch.get_dispatcher_num(len_ids, len_u_ids)
    logging.info("WaAccountId2#id数量为 = %s, 用户数量为= %s", len_ids, len_u_ids)
    logging.info("WaAccountId2#每个用户分配Id数量为 = %s, 剩余未分配的数量为= %s", div_num, mod_num)

    bat_aid_record_list: List[WaUserIdRecord2] = []

    u_record_map, max_num = dispatch.user_num_record2(WaUserIdRecord2.objects, u_ids, RECORD_TYPE_WA_ID2)
    add_u_ids = set()

    def add_record(_u_id, _a_id):
        _num = u_record_map.get(_u_id)
        logging.info("WaAccountId2#将 %s 分配给 %s 用户当前数量为 = %s", _a_id, _u_id, _num)
        if _num is None:
            _num = 1
        else:
            _num += 1
        add_u_ids.add(_u_id)
        u_record_map[_u_id] = _num
        bat_aid_record_list.append(
            WaUserIdRecord2(
                user_id=_u_id,
                account_id=_a_id,
                used=UsedStatus.Default,
                create_time=time_utils.get_now_bj_time_str(),
                update_time=time_utils.get_now_bj_time_str()
            )
        )

    logging.info("WaAccountId2#处理数据分发用户")
    # dispatch.dispatcher_user(a_ids, u_ids, div_num, mod_num, add_record)
    dispatch.dispatcher_user2(a_ids, u_ids, u_record_map.copy(), max_num, add_record)
    logging.info("WaAccountId2#开始处理AccountIdRecord数据批量插入")

    if len(bat_aid_record_list) == 0:
        return -1, "分配失败，原因:len = 0"

    with transaction.atomic():
        logging.info("WaAccountId2#开始数据库事务")
        logging.info("WaAccountId2#插入Id记录信息")
        # 插入记录信息
        WaUserIdRecord2.objects.bulk_create(bat_aid_record_list)
        logging.info("WaAccountId2#开始处理用户当天数据数量")
        dispatch.handle_user_record(u_record_map, RECORD_TYPE_WA_ID2)
        logging.info("WaAccountId2#将数据 bind 设置为True ids = %s", a_ids)
        WaAccountId2.objects.filter(id__in=a_ids).update(is_bind=True)

    return 0, f"成功分配{len_ids}条数据到{len(add_u_ids)}个业务员手中"


def dispatcher_account_qr(is_all: bool) -> Tuple[int, str]:
    warnings.warn("deprecated", DeprecationWarning)
    logging.info("WaAccountQr2#处理二维码数据分发 is_all = %s", is_all)
    # 用户表id列表和长度
    u_ids, len_u_ids = dispatch.get_business_user_ids2(USER_BACK_TYPE_WA2)
    logging.info("WaAccountQr2#查询到业务员数量为 = %s", len_u_ids)
    if len_u_ids == 0:
        return -1, "未找到可用的业务员"
    # AccountId表数据
    data_ids, len_ids = dispatch.get_account_list(WaAccountQr2.objects, is_all)
    if len_ids == 0:
        if is_all:
            return -1, "未找到可分配的数据"
        return -1, "未找到当日可分配的数据"
    logging.info("WaAccountQr2#查询到当天新增的数据量为 = %s", len_ids)
    div_num, mod_num = dispatch.get_dispatcher_num(len_ids, len_u_ids)
    logging.info("WaAccountQr2#二维码数量为 = %s, 用户数量为= %s", len_ids, len_u_ids)
    logging.info("WaAccountQr2#个用户分配Id数量为 = %s, 剩余未分配的数量为= %s", div_num, mod_num)
    bat_aid_record_list: List[WaUserQrRecord2] = []
    u_record_map, max_num = dispatch.user_num_record2(WaUserQrRecord2.objects, u_ids, RECORD_TYPE_WA_QR2)
    add_u_ids = set()

    def add_record(_u_id, _a_id):
        logging.info("add_record = uid = %s, id = %s", _u_id, _a_id)
        _num = u_record_map.get(_u_id)
        if _num is None:
            _num = 1
        else:
            _num += 1
        u_record_map[_u_id] = _num
        add_u_ids.add(_u_id)
        bat_aid_record_list.append(
            WaUserQrRecord2(
                user_id=_u_id,
                account_id=_a_id,
                create_time=time_utils.get_now_bj_time_str(),
                update_time=time_utils.get_now_bj_time_str()
            )
        )

    logging.info("WaAccountQr2#处理数据分发用户")
    # dispatch.dispatcher_user(data_ids, u_ids, div_num, mod_num, add_record)
    dispatch.dispatcher_user2(data_ids, u_ids, u_record_map.copy(), max_num, add_record)
    if len(bat_aid_record_list) == 0:
        return -1, "分配失败，原因:len = 0"
    logging.info("WaAccountQr2#开始处理 二维码-用户-记录 数据批量插入")
    with transaction.atomic():
        logging.info("WaAccountQr2#开始数据库事务")
        logging.info("WaAccountQr2#插入Id记录信息")
        WaUserQrRecord2.objects.bulk_create(bat_aid_record_list)
        logging.info("WaAccountQr2#开始处理用户当天数据数量")
        dispatch.handle_user_record(u_record_map, RECORD_TYPE_WA_QR2)
        logging.info("WaAccountQr2#将数据 bind 设置为True")
        WaAccountQr2.objects.filter(id__in=data_ids).update(is_bind=True)

    return 0, f"成功分配{len_ids}条数据到{len(add_u_ids)}个业务员手中"
