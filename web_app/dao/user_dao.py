import logging
from typing import Tuple

from django.db.models import Q

from util import utils
from web_app.model.users import User

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


def update_user(username: str, password: str, name: str):
    query = User.objects.filter(phone=username)
    if not query.exists():
        return User.objects.create(username=username, password=password, name=name)
    else:
        return query.update(password=password, name=name)


def user_list(start_row, end_row) -> tuple:
    """
    分页获取用户列表
    """
    query = User.objects
    res = query.all()[start_row: end_row]
    count = query.count()
    return utils.model2json(res), count


def delete_user(u_id, username: str = None) -> Tuple[bool, int]:
    """
    通过id或者用户名删除用户
    """
    q = Q(id=u_id) | Q(username=username)
    f = User.objects.filter(q)
    if f.exists():
        return f.delete()
    return False, -1
