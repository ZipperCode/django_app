import hashlib
import json
import logging
import os
import zipfile
from datetime import datetime
from typing import Iterable

from django.db.models import QuerySet, Q
from django.http import HttpRequest

CONFIG_DICT = []


def print_func(name):
    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>> {name} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


def check_and_create_dir(path, is_dir: bool = False):
    if path is None:
        raise ValueError('path not none')

    if is_dir:
        if not os.path.exists(path):
            os.makedirs(path, 755)
    else:
        pardir = os.path.abspath(os.path.join(path, os.path.pardir))
        if not os.path.exists(pardir):
            os.makedirs(pardir, 755)


def md5_encode(text) -> str:
    if text is None:
        return ""
    text = str(text)
    hl = hashlib.md5()
    hl.update(text.encode(encoding='utf-8'))
    return hl.hexdigest()


def page_query(request: HttpRequest):
    body = request_body(request)
    try:
        page = body.get("page", 1)
        limit = body.get('limit', 10)
        offset = (int(page) - 1) * int(limit)
        end_row = offset + int(limit)
    except ValueError:
        offset = 0
        end_row = 10
    return offset, end_row


def request_body(request: HttpRequest):
    return request.POST if request.method == "POST" else request.GET


def object_to_json(obj):
    if obj is None:
        return dict()
    if obj is str or obj is int or obj is float:
        return obj
    return dict([(kk, obj.__dict__[kk]) for kk in obj.__dict__.keys() if kk != "_state"])


def model2json(query) -> list:
    res = []
    if not isinstance(query, Iterable):
        return res
    for e in query:
        res.append(object_to_json(e))
    return res

def model_serialize(query):
    """
    @return list | dict | str
    """
    if isinstance(query, object):
        return object_to_json(query)
    elif isinstance(query, Iterable):
        res = []
        for e in query:
            res.append(object_to_json(e))
        return res
    else:
        return model2json(query)


def str_is_null(data):
    if data is None:
        return True
    return len(str(data)) <= 0


def is_float(s):
    try:  # 如果能运行float(s)语句，返回True（字符串s是浮点数）
        float(s)
        return True
    except ValueError:  # ValueError为Python的一种标准异常，表示"传入无效的参数"
        pass  # 如果引发了ValueError这种异常，不做任何事情（pass：不做任何事情，一般用做占位语句）
    return False


def is_int(s):
    if s is None:
        return False
    try:
        int(s)
        return True
    except ValueError:
        pass
    return False


def is_bool(s):
    try:
        if str(s).lower() == 'false':
            return True
        elif str(s).lower() == "true":
            return True
        return False
    except ValueError as e:
        logging.exception(e)
        return False


def is_bool_val(s):
    return True if str(s).lower() == 'true' else False


def get_date_q(cur_year, cur_month, cur_day) -> Q:
    logging.info("【get_date_q】 year = %s, month = %s, day = %s", cur_year, cur_month, cur_day)
    return Q(time__year=cur_year) & Q(time__month=cur_month) & Q(time__day=cur_day)


def get_tg_username(username: str, first_name: str = None, last_name: str = None, user_id=None) -> str:
    if not str_is_null(username):
        return username
    if not str_is_null(first_name):
        if not str_is_null(last_name):
            return f"{first_name}-{last_name}"
        return first_name
    return f"{user_id}"


def get_tg_full_name(first_name: str, last_name: str = None) -> str:
    if last_name:
        return f"{first_name} {last_name}"

    return f"{first_name}"


def flatmap(src):
    def _flatmap(_src, _dest=None, prefix=''):
        for k, v in _src.items():
            if isinstance(v, (list, tuple, set, dict)):
                _flatmap(v, _dest, prefix=prefix + k + '_')  # 递归调用
            else:
                _dest[prefix + k] = v

    dest = {}
    _flatmap(src, dest)
    return dest


def files2zip(fps, zip_fp):
    """
    多文件打包成zip
    :param fps:   [r'C:\1.txt', r'C:\2.txt', r'C:\3.txt'] 文件全路径的list
    :param zip_fp:  r'C:\files.zip'
    :param delete:  True    删除原文件
    :return:
    """
    if len(fps) == 0: return None
    if not zip_fp.endswith("zip"): return None
    zipf = zipfile.ZipFile(zip_fp, "w")  # 在路径中创建一个zip对象
    for fp in fps:
        fn = os.path.basename(fp)
        zipf.write(fp, fn)  # 第一个参数为该文件的全路径；第二个参数为文件在zip中的相对路径
    zipf.close()  # 关闭文件
    return zip_fp


def bytes2str(byte_str: str) -> str:
    if str_is_null(byte_str):
        return ""
    try:
        return str(bytes(list(map(lambda x: ord(x), list(byte_str)))), 'utf8')
    except BaseException:
        pass
    return byte_str


def handle_uploaded_file(path, f):
    try:
        parent_path = os.path.dirname(path)
        if not os.path.exists(parent_path):
            os.makedirs(parent_path)

        if os.path.exists(path):
            os.remove(path)

        with open(path, "wb+") as destination:
            for chunk in f.chunks():
                destination.write(chunk)
            return path
    except Exception:
        return None


if __name__ == '__main__':
    print(datetime.fromtimestamp(int(1667036550526) / 1000))
    s = "\xe6\x9d\x8e\xe6\x85\xa7\xe9\xa6\xa8"
    # s = "你好1"
    # print(str(bytes(list(map(lambda x: ord(x), list(s)))), 'utf8'))
    print(bytes2str(s))
    pass
