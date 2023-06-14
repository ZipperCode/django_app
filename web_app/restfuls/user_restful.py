import logging
import os

from django.db.models import Q
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from util import utils, http_utils
from util.restful import RestResponse, CJsonEncoder
from web_app.dao import user_dao
from web_app.decorators.admin_decorator import log_func
from web_app.model.users import User
from web_app.settings import BASE_DIR

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


@csrf_exempt
def register(request: HttpRequest):
    body = utils.request_body(request)
    username = body.get("username", "")
    password = body.get('password', "")
    name = body.get('name', "")
    logging.info("register#username = " + str(username))
    logging.info("register#password = " + str(password))
    if utils.str_is_null(str(username)):
        return http_utils.ret_error("phone is null")
    if utils.str_is_null(str(password)):
        return http_utils.ret_error("password is null")

    if User.objects.filter(phone=username, password=password).exists():
        return http_utils.ret_error("账号已经注册")

    user = User.objects.create(phone=username, password=password, name=name)

    return RestResponse.success()


@csrf_exempt
def update_user(request: HttpRequest):
    body = utils.request_body(request)
    username = body.get("username", "")
    password = body.get('password', "")
    name = body.get('name', "")
    logging.info("update_user#username = " + str(username))
    logging.info("update_user#password = " + str(password))
    logging.info("update_user#name = " + str(name))
    if utils.str_is_null(str(username)):
        return http_utils.ret_error("username is null")
    if utils.str_is_null(str(password)):
        return http_utils.ret_error("password is null")
    user_dao.update_user(username, password, name)
    return RestResponse.success()


@csrf_exempt
def login(request: HttpRequest):
    body = utils.request_body(request)
    username = body.get("username", "")
    password = body.get('password', "")
    logging.info("login#username = " + str(username))
    logging.info("login#password = " + str(password))
    if utils.str_is_null(str(username)):
        return http_utils.ret_error("username is null")
    if utils.str_is_null(str(password)):
        return http_utils.ret_error("password is null")
    query = User.objects.filter(username=username, password=password)
    if not query.exists():
        return RestResponse.failure("登录失败，账号或密码错误")
    else:
        user = query.first()
    user.password = ''
    return RestResponse.success(data=user)


def modify_password(request: HttpRequest):
    body = utils.request_body(request)
    username = body.get("username", "")
    password = body.get('password', "")
    password_new = body.get('password_new', "")
    password_new2 = body.get('password_new2', "")
    logging.info("modify_password#username = " + str(username))
    logging.info("modify_password#password = " + str(password))
    logging.info("modify_password#password_new = " + str(password_new))
    logging.info("modify_password#password_new2 = " + str(password_new2))
    if utils.str_is_null(str(username)):
        return RestResponse.failure("用户名不能为空")
    if utils.str_is_null(password):
        return RestResponse.failure("原密码不能为空")
    if utils.str_is_null(password_new):
        return RestResponse.failure("新密码不能为空")
    if utils.str_is_null(password_new2):
        return RestResponse.failure("确认密码不能为空")
    if str(password_new) != str(password_new2):
        return RestResponse.failure("新密码与确认密码不一致")

    query = User.objects.filter(username=username, password=password)
    if not query.exists():
        return RestResponse.failure("账号或密码错误，无法修改")

    user = query.filter()
    user.update(password=password_new)
    return RestResponse.success("密码修改成功")


def user_list(request: HttpRequest):
    start_row, end_row = utils.page_query(request)
    data, count = user_dao.user_list(start_row, end_row)
    result = {
        'code': 0,
        "count": count,
        'data': data
    }
    return RestResponse.success(data=result)


@log_func
def user_add(request: HttpRequest):
    body = utils.request_body(request)
    username = body.get("username", "")
    password = body.get('password', '')
    name = body.get('name', '')
    logging.info("user_add#username = " + str(username))
    logging.info("user_add#password = " + str(password))
    logging.info("user_add#name = " + str(name))
    if utils.str_is_null(str(username)):
        return RestResponse.failure("添加失败，用户名不能为空")
    if utils.str_is_null(password):
        return RestResponse.failure("添加失败，密码不能为空")
    query = User.objects.filter(username=username)
    if query.exists():
        return RestResponse.failure("添加失败，用户已存在")

    create_user = User.objects.create(username=username, password=password, name=name)
    create_user.password = ''
    return RestResponse.success(data=utils.object_to_json(create_user))


@log_func
def user_update(request: HttpRequest):
    body = utils.request_body(request)
    u_id = body.get("id", "")
    username = body.get("username", "")
    if utils.str_is_null(username) or (not str(u_id).isdigit() and int(u_id) <= 0):
        RestResponse.failure("参数错误，需要username或id")
    q = Q(id=u_id) or Q(username=username)
    query = User.objects.filter(q)
    if not query.exists():
        return RestResponse.failure("更新失败，记录不存在")

    password = body.get('password', '')
    if utils.str_is_null(password):
        return RestResponse.failure("更新失败，密码不能为空")
    name = body.get('name', '')
    rows = query.update(password=password, name=name)
    return RestResponse.success(data={
        'rows': rows
    })


@log_func
def user_del(request: HttpRequest):
    body = utils.request_body(request)
    u_id = body.get("id", "")
    username = body.get("username", "")
    if utils.str_is_null(username) or (not str(u_id).isdigit() and int(u_id) <= 0):
        RestResponse.failure("参数错误，需要username或id")
    q = Q(id=u_id) or Q(username=username)
    query = User.objects.filter(q)
    if not query.exists():
        return RestResponse.failure("删除失败，记录不存在")
    deleted, del_count = query.delete()
    return RestResponse.success(data={
        'deleted': deleted,
        'delete_count': del_count
    })


def file_down(request, name: str):
    p = os.path.join(BASE_DIR, "data", name)
    logging.info("filedown p = " + str(p))

    if not os.path.exists(p):
        p = os.path.join(BASE_DIR, "data", "app-release.apk")
    logging.info("filedown p1 = " + str(p))
    if not os.path.exists(p):
        return HttpResponse("resources not found")
    file = open(p, 'rb')
    file_name = os.path.basename(p)
    response = StreamingHttpResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="' + str(file_name) + '"'
    return response
