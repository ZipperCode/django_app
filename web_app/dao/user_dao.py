import json
import logging
from typing import Tuple

from django.db.models import Q
from django.http import HttpRequest

from util import utils
from web_app.model.users import User

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


def get_user(request: HttpRequest):
    user = request.session.get("user")
    if user is None:
        return None
    if user.get("username") is None:
        return None
    query = User.objects.filter(username=user.get('username'))
    if query.exists():
        return query.first()
    return None


def update_user(username: str, password: str, name: str, role):
    query = User.objects.filter(phone=username)
    if not query.exists():
        return User.objects.create(username=username, password=password, name=name, role=role)
    else:
        return query.update(password=password, name=name)


def user_list(start_row, end_row) -> tuple:
    """
    分页获取用户列表
    """
    query = User.objects
    res = query.values('id', 'username', 'name', 'is_admin', 'create_time', 'update_time')[start_row: end_row]
    count = query.count()
    return list(res), count


def delete_user(u_id, username: str = None) -> Tuple[bool, int]:
    """
    通过id或者用户名删除用户
    """
    q = Q(id=u_id) | Q(username=username)
    f = User.objects.filter(q)
    if f.exists():
        return f.delete()
    return False, -1
