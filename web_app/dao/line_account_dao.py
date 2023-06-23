import datetime
import logging
from typing import List, Tuple, Dict

from django.db import transaction
from django.db.models import QuerySet, F

from util import utils, time_utils
from util.time_utils import convert_date, convert_time
from web_app.decorators.admin_decorator import log_func
from web_app.model.accounts import AccountId, AccountQr, LineUserAccountIdRecord, LineUserAccountQrRecord
from web_app.model.users import User, USER_ROLE_BUSINESS, USER_ROLE_UPLOADER, UserAccountRecord, RECORD_TYPE_LINE_ID
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
    query.filter(op_user__isnull=False)
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
    if user.role == USER_ROLE_UPLOADER:
        logging.info("当前用户是角色是上传人，取当天上传的数据")
        start_t, end_t = time_utils.get_cur_day_time_range()
        query = query.filter(create_time__gte=start_t, create_time__lt=end_t, op_user__id=user.id)

    res = list(
        query.values(
            'id', 'account_id', 'country', 'age', 'work', 'money', 'mark', 'used', 'is_bind',
            'op_user__username', 'create_time', 'update_time'
        )
    )[start_row: end_row]

    return list(res), query.count()


@log_func
def search_account_qr_page(body, start_row, end_row, user: User):
    query = filter_field(AccountQr.objects, body)
    qr_content = body.get("qr_content")
    if not utils.str_is_null(qr_content):
        query = query.filter(qr_content__contains=qr_content)
    if user.role == USER_ROLE_UPLOADER:
        logging.info("当前用户是角色是上传人，取当天上传的数据")
        start_t, end_t = time_utils.get_cur_day_time_range()
        query = query.filter(create_time__gte=start_t, create_time__lt=end_t, op_user__id=user.id)

    res = list(
        query.values(
            'id', 'qr_content', 'qr_path', 'country', 'age', 'work', 'money', 'mark', 'used', 'is_bind',
            'op_user__username', 'create_time', 'update_time'
        )
    )[start_row: end_row]

    return list(res), query.count()


def _handle_user_record(u_record_map):
    start_t, end_t = time_utils.get_cur_day_time_range()
    for k, v in u_record_map.items():
        q = UserAccountRecord.objects.filter(user_id=k, create_time__gte=start_t, create_time__lt=end_t)
        if q.exists():
            q.update(data_num=F('data_num') + v, update_time=time_utils.get_now_bj_time())
        else:
            UserAccountRecord.objects.create(
                user_id=k,
                data_num=v,
                type=RECORD_TYPE_LINE_ID,
                create_time=time_utils.get_now_bj_time(),
                update_time=time_utils.get_now_bj_time()
            )


def dispatcher_account_id(is_all: bool = False) -> Tuple[int, str]:
    logging.info("lineAccountId#处理id数据分发")
    # 用户表id列表和长度
    u_ids, len_u_ids = dispatch.get_business_user_ids()
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

    u_record_map: Dict[int, int] = dict()

    def add_record(_u_id, _a_id):
        _num = u_record_map.get(_u_id)
        if _num is None:
            _num = 1
        else:
            _num += 1
        u_record_map[_u_id] = _num
        bat_aid_record_list.append(
            LineUserAccountIdRecord(
                user_id=_u_id,
                account_id=_a_id,
                used=False,
                create_time=time_utils.get_now_bj_time(),
                update_time=time_utils.get_now_bj_time()
            )
        )

    logging.info("lineAccountId#处理数据分发用户")
    dispatch.dispatcher_user(a_ids, u_ids, div_num, mod_num, add_record)
    logging.info("lineAccountId#开始处理AccountIdRecord数据批量插入")

    if len(bat_aid_record_list) == 0:
        return -1, "分配失败，原因:len = 0"

    with transaction.atomic():
        logging.info("lineAccountId#开始数据库事务")
        logging.info("lineAccountId#插入Id记录信息")
        # 插入记录信息
        LineUserAccountIdRecord.objects.bulk_create(bat_aid_record_list)
        logging.info("lineAccountId#开始处理用户当天数据数量")
        _handle_user_record(u_record_map)
        logging.info("lineAccountId#将数据 bind 设置为True ids = %s", a_ids)
        AccountId.objects.filter(id__in=a_ids).update(is_bind=True)

    return 0, f"成功分配{len_ids}条数据到{len_u_ids}个业务员手中"


def dispatcher_account_qr(is_all: bool) -> Tuple[int, str]:
    logging.info("lineAccountQr#处理二维码数据分发")
    # 用户表id列表和长度
    u_ids, len_u_ids = dispatch.get_business_user_ids()
    logging.info("lineAccountQr#查询到业务员数量为 = %s", len_u_ids)
    if len_u_ids == 0:
        return -1, "未找到可用的业务员"
    # AccountId表数据
    data_ids, len_ids = dispatch.get_account_list(AccountQr.objects, is_all)
    if len_ids == 0:
        return -1, "未找到当日可分配的数据"
    logging.info("lineAccountQr#查询到当天新增的数据量为 = %s", len_ids)
    div_num, mod_num = dispatch.get_dispatcher_num(len_ids, len_u_ids)
    logging.info("lineAccountQr#二维码数量为 = %s, 用户数量为= %s", len_ids, len_u_ids)
    logging.info("lineAccountQr#个用户分配Id数量为 = %s, 剩余未分配的数量为= %s", div_num, mod_num)
    bat_aid_record_list: List[LineUserAccountQrRecord] = []
    u_record_map: Dict[int, int] = dict()

    def add_record(_u_id, _a_id):
        _num = u_record_map.get(_u_id)
        if _num is None:
            _num = 1
        else:
            _num += 1
        bat_aid_record_list.append(
            LineUserAccountQrRecord(
                user_id=_u_id,
                account_id=_a_id,
                create_time=time_utils.get_now_bj_time(),
                update_time=time_utils.get_now_bj_time()
            )
        )

    logging.info("lineAccountQr#处理数据分发用户")
    dispatch.dispatcher_user(data_ids, u_ids, div_num, mod_num, add_record)
    if len(bat_aid_record_list) == 0:
        return -1, "分配失败，原因:len = 0"
    logging.info("lineAccountQr#开始处理 二维码-用户-记录 数据批量插入")
    with transaction.atomic():
        logging.info("lineAccountQr#开始数据库事务")
        logging.info("lineAccountQr#插入Id记录信息")
        LineUserAccountQrRecord.objects.bulk_create(bat_aid_record_list)
        logging.info("lineAccountQr#开始处理用户当天数据数量")
        _handle_user_record(u_record_map)
        logging.info("lineAccountQr#将数据 bind 设置为True")
        AccountId.objects.filter(id__in=data_ids).update(is_bind=True)

    return 0, f"成功分配{len_ids}条数据到{len_u_ids}个业务员手中"
