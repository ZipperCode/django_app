from datetime import datetime, date

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse

from util import time_utils, utils


class CJsonEncoder(DjangoJSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return time_utils.convert_timezone(obj).strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(obj, date):
                return time_utils.convert_timezone(obj).strftime('%Y-%m-%d')
            else:
                # return json.JSONEncoder.default(self, obj)
                return DjangoJSONEncoder.default(self, obj)
        except TypeError:
            return utils.object_to_json(obj)


class RestResponse(JsonResponse):

    def __init__(self, data):
        super().__init__(data, encoder=CJsonEncoder)

    @classmethod
    def success(cls, msg: str = "操作成功", data=None):
        return RestResponse({
            'code': 0,
            'msg': msg,
            'data': data
        })

    @classmethod
    def success_list(cls, msg: str = "操作成功", count=0, data: list = None):
        return RestResponse({
            'code': 0,
            'msg': msg,
            'count': count,
            'data': data
        })

    @classmethod
    def failure(cls, msg: str):
        return RestResponse({
            'code': -1,
            'msg': msg
        })
