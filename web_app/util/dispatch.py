import logging
from typing import Tuple, List

from util import time_utils
from web_app.model.users import USER_ROLE_BUSINESS, User


def get_user_ids() -> Tuple[list, int]:
    u_ids = list(map(lambda x: x.get('id'), list(User.objects.filter(role=USER_ROLE_BUSINESS).values('id'))))
    len_ids = len(u_ids)
    return u_ids, len_ids


def get_account_list(objects) -> Tuple[list, int]:
    cur_start_t, cur_end_t = time_utils.get_cur_day_time_range()
    query_list = list(
        objects.filter(
            used=False, create_time__gte=cur_start_t, create_time__lt=cur_end_t
        ).all()
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
            while j < len_ids and a_index < len_ids:
                _id = ids_[a_index]
                u_id = u_ids[j]
                a_index += 1
                func(u_id, _id)

    if mod_num > 0:
        logging.info("dispatcher#将剩余的数据，依次分配到用户")
        i = 0
        while i < mod_num and a_index < len_ids:
            u_id = u_ids[i]
            _id = ids_[a_index]
            a_index += 1
            func(u_id, _id)
