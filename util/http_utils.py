import json
import logging
from datetime import date, datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import QuerySet
from django.http import HttpRequest, JsonResponse

from util import utils


class CJsonEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            # return json.JSONEncoder.default(self, obj)
            return DjangoJSONEncoder.default(self, obj)


def print_body(name, body):
    try:
        logging.info(f"{name} >> body = %s", str(body))
    except Exception:
        pass


def object_to_json(obj):
    return dict([(kk, obj.__dict__[kk]) for kk in obj.__dict__.keys() if kk != "_state"])


def query_list_request(request: HttpRequest, query: QuerySet):
    start_row, end_row = utils.page_query(request)
    res = query.all()[start_row: end_row]
    count = query.count()
    result = {
        "code": 0,
        "count": count,
        "data": utils.model2json(res)
    }
    return JsonResponse(result, encoder=CJsonEncoder)


def delete_request(request: HttpRequest, query: QuerySet):
    body = utils.request_body(request)
    pk_id = body.get("id", 0)
    if int(pk_id) == 0:
        return JsonResponse({
            "code": -1,
            "msg": "删除失败，id错误"
        })

    exists = query.filter(id=pk_id)
    count = exists.count()
    logging.info("delete_request >> count = %s, exists = %s", count, type(exists))
    if count <= 0:
        return JsonResponse({
            "code": -1,
            "msg": "删除失败，数据不存在"
        })
    exists.delete()
    return JsonResponse({
        "code": 0,
        "msg": "删除成功"
    })


def ret_error(msg):
    return JsonResponse({
        "code": -1,
        "msg": msg
    })


def ret_success(msg, data: object = None):
    return JsonResponse({
        "code": 0,
        "msg": f"{msg}",
        "data": {} if data is None else object_to_json(data)
    }, encoder=CJsonEncoder)


def ret_upd_res(exists, query):
    result = {
        "code": -1
    }
    if isinstance(query, int) and query > 0:
        result['code'] = 0
        result['msg'] = "数据更新成功"
        result['data'] = object_to_json(exists.get())
    else:
        result['msg'] = "数据更新失败，请重试"

    return JsonResponse(result)


def ret_add_res(query, cls):
    result = {
        "code": -1
    }
    if isinstance(query, cls) and query.id > 0:
        result['code'] = 0
        result['msg'] = "数据添加成功"
    else:
        result['msg'] = "添加数据失败"

    return JsonResponse(result)


def check_user_id(user_id) -> bool:
    if user_id is None:
        return False

    if utils.str_is_null(user_id):
        return False

    if not str(user_id).isdigit():
        return False

    return int(user_id) > 0