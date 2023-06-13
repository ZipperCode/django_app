import logging
import os

from django.http import HttpRequest, HttpResponse, StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from util import utils, http_utils
from util.restful import RestResponse, CJsonEncoder
from web_app.dao import user_dao
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
    result = {
        'code': 0,
        "count": 2,
        'data': [
            {
                'id':1,
                'username': 'admin',
                'name': 'admin',
                'create_time': '2023-1-1 11:11:11',
                'update_time': '2023-1-1 11:11:11',
            },
            {
                'id': 1,
                'username': 'admin',
                'name': 'admin',
                'create_time': '2023-1-1 11:11:11',
                'update_time': '2023-1-1 11:11:11',
            },
            {
                'id': 1,
                'username': 'admin',
                'name': 'admin',
                'create_time': '2023-1-1 11:11:11',
                'update_time': '2023-1-1 11:11:11',
            },
        ]
    }
    return JsonResponse(result, encoder=CJsonEncoder)


def user_add(request: HttpRequest):

    return RestResponse.failure("not impl")

def user_update(request: HttpRequest):

    return RestResponse.failure("not impl")

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
