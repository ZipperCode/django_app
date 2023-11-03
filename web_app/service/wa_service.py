import logging
from typing import Tuple, Optional

from django.db import transaction
from django.db.models import QuerySet, Model

from util import utils, time_utils
from web_app.decorators.admin_decorator import log_func
from web_app.model.const import UsedStatus
from web_app.model.users import User, USER_ROLE_UPLOADER, USER_BACK_TYPE_WA, USER_BACK_TYPE_WA2, USER_BACK_TYPE_WA3, \
    USER_BACK_TYPE_WA4, USER_BACK_TYPE_WA5, RECORD_TYPE_WA_ID, RECORD_TYPE_WA_ID2, RECORD_TYPE_WA_ID3, \
    RECORD_TYPE_WA_ID4, RECORD_TYPE_WA_ID5, WA_TYPES
from web_app.model.wa_accounts import WaAccountId, WaUserIdRecord, WaAccountQr, WaUserQrRecord
from web_app.model.wa_accounts2 import WaAccountId2, WaUserIdRecord2, WaAccountQr2, WaUserQrRecord2
from web_app.model.wa_accounts3 import WaAccountId3, WaUserIdRecord3, WaAccountQr3, WaUserQrRecord3
from web_app.model.wa_accounts4 import WaUserQrRecord4, WaAccountQr4, WaUserIdRecord4, WaAccountId4
from web_app.model.wa_accounts5 import WaUserQrRecord5, WaAccountQr5, WaUserIdRecord5, WaAccountId5
from web_app.util import rest_list_util, dispatch

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


def wa_id_query_set(back_type) -> Optional[QuerySet]:
    queryset = None
    if not utils.is_int(back_type):
        return queryset
    back_type = int(back_type)

    if back_type == USER_BACK_TYPE_WA:
        queryset = WaAccountId.objects
    elif back_type == USER_BACK_TYPE_WA2:
        queryset = WaAccountId2.objects
    elif back_type == USER_BACK_TYPE_WA3:
        queryset = WaAccountId3.objects
    elif back_type == USER_BACK_TYPE_WA4:
        queryset = WaAccountId4.objects
    elif back_type == USER_BACK_TYPE_WA5:
        queryset = WaAccountId5.objects
    return queryset


def check_id(a_id) -> bool:
    for t in WA_TYPES:
        if wa_id_query_set(t).filter(account_id=a_id).exists():
            logging.info("check_id#%s#id = %s", t, a_id)
            return True
    return False


def check_id_list(ids):
    ids = list(ids)
    for t in WA_TYPES:
        queryset = wa_qr_queryset(t)
        exists_query = queryset.filter(account_id__in=ids)
        for query in exists_query:
            i = ids.index(query.account_id)
            if i >= 0:
                ids.pop(i)
            if len(ids) == 0:
                return True

    return False


def wa_id_record_queryset(back_type) -> Optional[QuerySet]:
    record_query = None
    if not utils.is_int(back_type):
        return None
    back_type = int(back_type)
    if back_type == USER_BACK_TYPE_WA:
        record_query = WaUserIdRecord.objects
    elif back_type == USER_BACK_TYPE_WA2:
        record_query = WaUserIdRecord2.objects
    elif back_type == USER_BACK_TYPE_WA3:
        record_query = WaUserIdRecord3.objects
    elif back_type == USER_BACK_TYPE_WA4:
        record_query = WaUserIdRecord4.objects
    elif back_type == USER_BACK_TYPE_WA5:
        record_query = WaUserIdRecord5.objects

    return record_query


def wa_qr_queryset(back_type) -> Optional[QuerySet]:
    queryset = None
    if not utils.is_int(back_type):
        return None
    back_type = int(back_type)
    if back_type == USER_BACK_TYPE_WA:
        queryset = WaAccountQr.objects
    elif back_type == USER_BACK_TYPE_WA2:
        queryset = WaAccountQr2.objects
    elif back_type == USER_BACK_TYPE_WA3:
        queryset = WaAccountQr3.objects
    elif back_type == USER_BACK_TYPE_WA4:
        queryset = WaAccountQr4.objects
    elif back_type == USER_BACK_TYPE_WA5:
        queryset = WaAccountQr5.objects
    return queryset


def check_qr(qr_content) -> bool:
    for t in WA_TYPES:
        if wa_qr_queryset(t).filter(qr_content=qr_content, op_user__isnull=False).exists():
            logging.info("check_qr#%s#qr_content = %s", t, qr_content)
            return True

    return False


def wa_qr_record_queryset(back_type) -> Optional[QuerySet]:
    record_query = None
    if not utils.is_int(back_type):
        return None
    back_type = int(back_type)
    if back_type == USER_BACK_TYPE_WA:
        record_query = WaUserQrRecord.objects
    elif back_type == USER_BACK_TYPE_WA2:
        record_query = WaUserQrRecord2.objects
    elif back_type == USER_BACK_TYPE_WA3:
        record_query = WaUserQrRecord3.objects
    elif back_type == USER_BACK_TYPE_WA4:
        record_query = WaUserQrRecord4.objects
    elif back_type == USER_BACK_TYPE_WA5:
        record_query = WaUserQrRecord5.objects

    return record_query


def wa_id_create_model(back_type, **create_dict):
    model = None
    if not utils.is_int(back_type):
        return None
    back_type = int(back_type)
    if back_type == USER_BACK_TYPE_WA:
        model = WaAccountId(**create_dict)
    elif back_type == USER_BACK_TYPE_WA2:
        model = WaAccountId2(**create_dict)
    elif back_type == USER_BACK_TYPE_WA3:
        model = WaAccountId3(**create_dict)
    elif back_type == USER_BACK_TYPE_WA4:
        model = WaAccountId4(**create_dict)
    elif back_type == USER_BACK_TYPE_WA5:
        model = WaAccountId5(**create_dict)

    return model


def wa_id_record_create_model(back_type, **create_dict):
    model = None
    if not utils.is_int(back_type):
        return None
    back_type = int(back_type)
    if back_type == USER_BACK_TYPE_WA:
        model = WaUserIdRecord(**create_dict)
    elif back_type == USER_BACK_TYPE_WA2:
        model = WaUserIdRecord2(**create_dict)
    elif back_type == USER_BACK_TYPE_WA3:
        model = WaUserIdRecord3(**create_dict)
    elif back_type == USER_BACK_TYPE_WA4:
        model = WaUserIdRecord4(**create_dict)
    elif back_type == USER_BACK_TYPE_WA5:
        model = WaUserIdRecord5(**create_dict)

    return model


def wa_qr_create_model(back_type, **create_dict):
    model = None
    if not utils.is_int(back_type):
        return None
    back_type = int(back_type)
    if back_type == USER_BACK_TYPE_WA:
        model = WaAccountQr(**create_dict)
    elif back_type == USER_BACK_TYPE_WA2:
        model = WaAccountQr2(**create_dict)
    elif back_type == USER_BACK_TYPE_WA3:
        model = WaAccountQr3(**create_dict)
    elif back_type == USER_BACK_TYPE_WA4:
        model = WaAccountQr4(**create_dict)
    elif back_type == USER_BACK_TYPE_WA5:
        model = WaAccountQr5(**create_dict)

    return model


def get_record_type(back_type) -> int:
    record_type = 0
    if not utils.is_int(back_type):
        return 0
    back_type = int(back_type)
    if back_type == USER_BACK_TYPE_WA:
        record_type = RECORD_TYPE_WA_ID
    elif back_type == USER_BACK_TYPE_WA2:
        record_type = RECORD_TYPE_WA_ID2
    elif back_type == USER_BACK_TYPE_WA3:
        record_type = RECORD_TYPE_WA_ID3
    elif back_type == USER_BACK_TYPE_WA4:
        record_type = RECORD_TYPE_WA_ID4
    elif back_type == USER_BACK_TYPE_WA5:
        record_type = RECORD_TYPE_WA_ID5

    return record_type


def wa_qr_record_create_model(back_type, **create_dict):
    model = None
    if not utils.is_int(back_type):
        return None
    back_type = int(back_type)
    if back_type == USER_BACK_TYPE_WA:
        model = WaUserQrRecord(**create_dict)
    elif back_type == USER_BACK_TYPE_WA2:
        model = WaUserQrRecord2(**create_dict)
    elif back_type == USER_BACK_TYPE_WA3:
        model = WaUserQrRecord3(**create_dict)
    elif back_type == USER_BACK_TYPE_WA4:
        model = WaUserQrRecord4(**create_dict)
    elif back_type == USER_BACK_TYPE_WA5:
        model = WaUserQrRecord5(**create_dict)

    return model


def search_aid_page(body, start_row, end_row, user: User, queryset: QuerySet):
    query = rest_list_util.search_account_common_field(queryset, body)
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
def search_aqr_page(body, start_row, end_row, user: User, queryset: QuerySet):
    query = rest_list_util.search_account_common_field(queryset, body)
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


def dispatcher_aid(queryset: QuerySet, back_type: int, record_queryset: QuerySet,
                   record_type: int, is_all: bool = False) -> Tuple[int, str]:
    logging.info("%s#处理id数据分发", back_type)
    # 用户表id列表和长度
    u_ids, len_u_ids = dispatch.get_business_user_ids2(back_type)
    logging.info("%s#查询到业务员数量为 = %s", back_type, len_u_ids)
    if len_u_ids == 0:
        return -1, "未找到可用的业务员"
    # AccountId表数据
    a_ids, len_ids = dispatch.get_account_list(queryset, is_all)
    logging.info("%s#a_ids= %s, len = %s", back_type, a_ids, len_ids)
    if len_ids == 0:
        if is_all:
            return -1, "未找到可分配的数据"
        return -1, "未找到当日可分配的数据"
    logging.info(f"{back_type}#查询到当天新增的数据量为 = %s", len_ids)
    div_num, mod_num = dispatch.get_dispatcher_num(len_ids, len_u_ids)
    logging.info(f"{back_type}#id数量为 = %s, 用户数量为= %s", len_ids, len_u_ids)
    logging.info(f"{back_type}#每个用户分配Id数量为 = %s, 剩余未分配的数量为= %s", div_num, mod_num)

    bat_aid_record_list = []

    u_record_map, max_num = dispatch.user_num_record2(record_queryset, u_ids, record_type)
    add_u_ids = set()

    def add_record(_u_id, _a_id):
        _num = u_record_map.get(_u_id)
        logging.info(f"{back_type}#将 %s 分配给 %s 用户当前数量为 = %s", _a_id, _u_id, _num)
        if _num is None:
            _num = 1
        else:
            _num += 1
        add_u_ids.add(_u_id)
        u_record_map[_u_id] = _num
        create_dict = {
            'user_id': _u_id,
            'account_id': _a_id,
            'used': UsedStatus.Default,
            'create_time': time_utils.get_now_bj_time_str(),
            'update_time': time_utils.get_now_bj_time_str()
        }
        model = wa_id_record_create_model(back_type, **create_dict)
        if model:
            bat_aid_record_list.append(model)
        else:
            logging.info(f"{back_type}#add_record_id 失败，创建model为空")

    logging.info(f"{back_type}#处理数据分发用户")
    dispatch.dispatcher_user3(a_ids, u_ids, u_record_map.copy(), max_num, add_record)
    logging.info(f"{back_type}#开始处理AccountIdRecord数据批量插入 记录 len = %s", len(bat_aid_record_list))

    if len(bat_aid_record_list) == 0:
        return -1, "分配失败，原因:len = 0"

    with transaction.atomic():
        logging.info(f"{back_type}#开始数据库事务")
        logging.info(f"{back_type}#插入Id记录信息")
        # 插入记录信息
        record_queryset.bulk_create(bat_aid_record_list)
        logging.info(f"{back_type}#开始处理用户当天数据数量")
        dispatch.handle_user_record(u_record_map, record_type)
        a_ids = list(map(lambda x: x.account_id, bat_aid_record_list))
        logging.info(f"{back_type}#将数据 bind 设置为True ids = %s", a_ids)
        queryset.filter(id__in=a_ids).update(is_bind=True)

    return 0, f"成功分配{len_ids}条数据到{len(add_u_ids)}个业务员手中"


def dispatcher_aqr(queryset: QuerySet, back_type: int, record_queryset: QuerySet,
                   record_type: int, is_all: bool) -> Tuple[int, str]:
    logging.info(f"{back_type}#处理二维码数据分发 is_all = %s", is_all)
    # 用户表id列表和长度
    u_ids, len_u_ids = dispatch.get_business_user_ids2(back_type)
    logging.info(f"{back_type}#查询到业务员数量为 = %s", len_u_ids)
    if len_u_ids == 0:
        return -1, "未找到可用的业务员"
    # AccountId表数据
    data_ids, len_ids = dispatch.get_account_list(queryset, is_all)
    if len_ids == 0:
        if is_all:
            return -1, "未找到可分配的数据"
        return -1, "未找到当日可分配的数据"
    logging.info(f"{back_type}#查询到当天新增的数据量为 = %s", len_ids)
    div_num, mod_num = dispatch.get_dispatcher_num(len_ids, len_u_ids)
    logging.info(f"{back_type}#二维码数量为 = %s, 用户数量为= %s", len_ids, len_u_ids)
    logging.info(f"{back_type}#个用户分配Id数量为 = %s, 剩余未分配的数量为= %s", div_num, mod_num)
    bat_aid_record_list = []
    u_record_map, max_num = dispatch.user_num_record2(record_queryset, u_ids, record_type)
    add_u_ids = set()

    def add_record(_u_id, _a_id):
        logging.info(f"{back_type}#add_record = uid = %s, id = %s", _u_id, _a_id)
        _num = u_record_map.get(_u_id)
        if _num is None:
            _num = 1
        else:
            _num += 1
        u_record_map[_u_id] = _num
        add_u_ids.add(_u_id)
        create_dict = {
            'user_id': _u_id,
            'account_id': _a_id,
            'used': UsedStatus.Default,
            'create_time': time_utils.get_now_bj_time_str(),
            'update_time': time_utils.get_now_bj_time_str()
        }
        model = wa_qr_record_create_model(back_type, **create_dict)
        if model:
            bat_aid_record_list.append(model)

    logging.info(f"{back_type}#处理数据分发用户")
    # dispatch.dispatcher_user(data_ids, u_ids, div_num, mod_num, add_record)
    dispatch.dispatcher_user3(data_ids, u_ids, u_record_map.copy(), max_num, add_record)
    if len(bat_aid_record_list) == 0:
        return -1, "分配失败，原因:len = 0"
    logging.info(f"{back_type}#开始处理 二维码-用户-记录 数据批量插入")
    with transaction.atomic():
        logging.info(f"{back_type}#开始数据库事务")
        logging.info(f"{back_type}#插入Id记录信息")
        record_queryset.bulk_create(bat_aid_record_list)
        logging.info(f"{back_type}#开始处理用户当天数据数量")
        dispatch.handle_user_record(u_record_map, record_type)
        data_ids = list(map(lambda x: x.account_id, bat_aid_record_list))
        logging.info(f"{back_type}#将数据 bind 设置为True ids = %s", data_ids)
        queryset.filter(id__in=data_ids).update(is_bind=True)

    return 0, f"成功分配{len_ids}条数据到{len(add_u_ids)}个业务员手中"
