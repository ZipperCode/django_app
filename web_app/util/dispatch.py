import logging
from typing import Tuple, List, Dict

from django.db import transaction
from django.db.models import QuerySet

from util import time_utils
from web_app.decorators.admin_decorator import log_func
from web_app.model.accounts import LineUserAccountIdRecord
from web_app.model.const import UsedStatus
from web_app.model.users import USER_ROLE_BUSINESS, User, UserAccountRecord, RECORD_TYPE_LINE_ID, RECORD_TYPE_NONE


@log_func
def get_business_user_ids2(back_type: int) -> Tuple[list, int]:
    logging.info("back_type = %s", back_type)
    query = User.objects.filter(role=USER_ROLE_BUSINESS, back_type=back_type, bind_dispatch=False).values('id')
    logging.info("获取到的用户列表为 = %s", list(query))
    u_ids = list(map(lambda x: x.get('id'), list(query)))
    len_ids = len(u_ids)
    return u_ids, len_ids


def get_account_list(objects, is_all: bool = False) -> Tuple[list, int]:
    cur_start_t, cur_end_t = time_utils.get_cur_day_time_range()
    filter_filed = {
        'is_bind': False,
        'used': UsedStatus.Default
    }
    if not is_all:
        logging.info("is_all = False, 分配当天")
        filter_filed['create_time__gte'] = cur_start_t
        filter_filed['create_time__lt'] = cur_end_t

    query_list = list(
        objects.filter(**filter_filed).all()
    )
    return list(map(lambda x: int(x.id), query_list)), len(query_list)


def get_dispatcher_num(len_: int, len_u: int) -> Tuple[int, int]:
    return int(len_ / len_u), int(len_ % len_u)


def dispatcher_user(ids_: List[int], u_ids: List[int], div_num: int, mod_num: int, func):
    logging.info("dispatcher#分发处理, div_num = %s, mod_num = %s", div_num, mod_num)
    len_ids = len(ids_)
    a_index = 0
    if div_num > 0:
        logging.info("dispatcher#平分数据到每个用户")
        i = 0
        while i < div_num and a_index < len_ids:
            j = 0
            while j < len(u_ids) and a_index < len_ids:
                _id = ids_[a_index]
                u_id = u_ids[j]
                a_index += 1
                func(u_id, _id)
                j += 1

    if mod_num > 0:
        logging.info("dispatcher#将剩余的数据，依次分配到用户")
        i = 0
        while i < mod_num and a_index < len_ids:
            u_id = u_ids[i]
            _id = ids_[a_index]
            a_index += 1
            func(u_id, _id)
            i += 1


def dispatcher_user2(ids: List[int], u_ids: List[int], user_num_map: Dict[int, int], max_num: int, func):
    logging.info("dispatcher2#分发处理， ids = %s", ids)
    logging.info("dispatcher2#分发处理， u_ids = %s", u_ids)
    logging.info("dispatcher2#分发处理， user_num_map = %s", user_num_map)
    logging.info("dispatcher2#分发处理， max_num = %s", max_num)
    a_index = 0
    len_ids = len(ids)
    len_u_ids = len(u_ids)
    min_num = max_num
    # 最小的数量
    for k, v in user_num_map.items():
        if v < min_num:
            min_num = v

    # 最大 - 最小 = 填充次数
    logging.info("dispatcher2#开始填充用户不满足的数量, 填充次数 = %s，最大 = %s, 最小 = %s", (max_num - min_num),
                 max_num, min_num)
    for i in range(0, max_num - min_num):
        for user_id, data_num in user_num_map.items():
            if a_index >= len_ids:
                break
            if data_num < max_num:
                func(user_id, ids[a_index])
                a_index += 1

    len_ids = len_ids - a_index
    a_index = 0
    div_num, mod_num = get_dispatcher_num(len_ids, len_u_ids)
    logging.info("dispatcher2#开始平均分配到每个用户, div_num = %s, mod_num = %s", div_num, mod_num)

    if div_num > 0:
        i = 0
        while i < div_num and a_index < len_ids:
            j = 0
            while j < len_u_ids and a_index < len_ids:
                _id = ids[a_index]
                u_id = u_ids[j]
                a_index += 1
                func(u_id, _id)
                j += 1
    logging.info("dispatcher#一轮分配结果完毕")
    if mod_num > 0:
        logging.info("dispatcher2#将剩余的数据，依次分配到用户")
        i = 0
        while i < mod_num and a_index < len_ids:
            u_id = u_ids[i]
            _id = ids[a_index]
            a_index += 1
            func(u_id, _id)
            i += 1


def dispatcher_user3(ids: List[int], u_ids: List[int], user_num_map: Dict[int, int], max_num: int, func):
    logging.info("dispatcher3#分发处理， ids = %s", ids)
    logging.info("dispatcher3#分发处理， u_ids = %s", u_ids)
    logging.info("dispatcher3#分发处理， user_num_map = %s", user_num_map)
    logging.info("dispatcher3#分发处理， max_num = %s", max_num)

    len_u_ids = len(u_ids)
    min_num = max_num
    # 最小的数量
    for k, v in user_num_map.items():
        if v < min_num:
            min_num = v
    # 最大 - 最小 = 填充次数
    logging.info("dispatcher3#开始填充用户不满足的数量, 填充次数 = %s，最大 = %s, 最小 = %s", (max_num - min_num),
                 max_num, min_num)

    for i in range(0, max_num - min_num):
        for user_id, data_num in user_num_map.items():
            if data_num < max_num and len(ids) > 0:
                _id = ids.pop()
                func(user_id, _id)

    if len(ids) <= 0:
        logging.info("dispatcher3#可分配id不足，退出分配")
        return
    len_ids = len(ids)
    div_num, mod_num = get_dispatcher_num(len_ids, len_u_ids)
    logging.info("dispatcher3#填充完毕，开始进行平均分配，剩余数量 = %s, div_num = %s, mod_num = %s",
                 len_ids, div_num, mod_num)
    logging.info("dispatcher3#开始进行分配，当前剩余可分配id列表 = %s", ids)

    if div_num > 0:
        logging.info("dispatcher3#可平分数量 = %s", div_num)
        for index in range(0, div_num):
            for u_id in u_ids:
                if len(ids) <= 0:
                    continue
                _id = ids.pop()
                func(u_id, _id)

    logging.info("dispatcher3#平分完毕，继续分配非平均部分 数量 = %s ids = %s", mod_num, ids)

    if mod_num > 0:
        for index in range(0, mod_num):
            for u_id in u_ids:
                if len(ids) <= 0:
                    continue
                _id = ids.pop()
                func(u_id, _id)

    logging.info("dispatcher3#全部分配完毕")


def handle_user_record(u_record_map, t: int = RECORD_TYPE_NONE):
    logging.info("保存数量值#recordMap = %s", u_record_map)
    start_t, end_t = time_utils.get_cur_day_time_range()
    for k, v in u_record_map.items():
        q = UserAccountRecord.objects.filter(user_id=k, create_time__gte=start_t, create_time__lt=end_t)
        if q.exists():
            q.update(data_num=v, update_time=time_utils.get_now_bj_time_str())
        else:
            UserAccountRecord.objects.create(
                user_id=k,
                data_num=v,
                type=t,
                create_time=time_utils.get_now_bj_time_str(),
                update_time=time_utils.get_now_bj_time_str()
            )


@log_func
def user_num_record2(objects: QuerySet, business_u_ids: list, t: int) -> Tuple[Dict[int, int], int]:
    """
    用户当天的数据数量
    @return 用户数量Map和最大数量元组 key: userid value = num
    """
    start_t, end_t = time_utils.get_cur_day_time_range()
    user_map: Dict[int, int] = dict()
    max_count = 0

    with transaction.atomic():
        for u in business_u_ids:
            _count = objects.filter(
                create_time__gte=start_t, create_time__lt=end_t, account__isnull=False, user_id=u
            ).count()
            logging.info("用户 %s 当天拥有的数据量为 %s", u, _count)
            user_map[u] = _count
            if max_count < _count:
                max_count = _count
            uar = UserAccountRecord.objects.filter(
                create_time__gte=start_t, create_time__lt=end_t, user_id=u, type=t
            )
            if uar.exists():
                uar.update(data_num=_count)

    logging.info("user_num_record#最大用户拥有的数据数量 %s, max_count = %s", user_map, max_count)
    return user_map, max_count
