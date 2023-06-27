import logging
import os

from django.db.models import Q
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse, JsonResponse, FileResponse
from django.utils.encoding import escape_uri_path
from django.views.decorators.csrf import csrf_exempt

from util import utils, http_utils, time_utils
from util.restful import RestResponse, CJsonEncoder
from web_app.dao import user_dao
from web_app.decorators.admin_decorator import log_func, op_admin, api_op_user
from web_app.model.users import User, USER_BACK_TYPE_NONE, USER_BACK_TYPE_WA, USER_BACK_TYPE_LINE
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
    role = body.get('role', 2)
    logging.info("update_user#username = " + str(username))
    logging.info("update_user#password = " + str(password))
    logging.info("update_user#name = " + str(name))
    if utils.str_is_null(str(username)):
        return http_utils.ret_error("username is null")
    if utils.str_is_null(str(password)):
        return http_utils.ret_error("password is null")
    user_dao.update_user(username, password, name, role)
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
    request.session['user'] = {
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'is_admin': user.is_admin,
        'role': user.role,
        'back_type': user.back_type,
        'bind_dispatch': user.bind_dispatch
    }
    return RestResponse.success("登录成功")


@log_func
@api_op_user
def modify_password(request: HttpRequest):
    body = utils.request_body(request)
    logging.info("修改密码#body = %s", body)
    username = body.get("username", "")
    password = body.get('password', "")
    password_new = body.get('password_new', "")
    password_new2 = body.get('password_new2', "")
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


@log_func
@op_admin
@api_op_user
def modify_password_admin(request: HttpRequest):
    body = utils.request_body(request)
    logging.info("管理员修改密码#body = %s", body)
    u_id = body.get("id", "")
    password_new = body.get('password_new', "")
    password_new2 = body.get('password_new2', "")

    if utils.str_is_null(u_id) or not utils.is_int(u_id):
        return RestResponse.failure("用户Id不能为空")
    if utils.str_is_null(password_new):
        return RestResponse.failure("新密码不能为空")
    if utils.str_is_null(password_new2):
        return RestResponse.failure("确认密码不能为空")
    if str(password_new) != str(password_new2):
        return RestResponse.failure("新密码与确认密码不一致")

    user = User.objects.filter(id=u_id)
    if not user.exists():
        return RestResponse.failure("修改失败，记录不存在")
    user.update(password=password_new)
    return RestResponse.success("密码修改成功")


@log_func
def user_list(request: HttpRequest):
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)
    logging.info("用户列表# body = %s", body)

    username = body.get('username', "")
    role = body.get('role', "")

    user_query = User.objects

    if not utils.str_is_null(username):
        user_query = user_query.filter(username__contains=username)

    if not utils.str_is_null(role) or utils.is_int(role):
        user_query = user_query.filter(role=int(role))

    query = user_query.values(
        'id', 'username', 'name', 'role', 'bind_dispatch', 'back_type', 'create_time', 'update_time'
    )[start_row: end_row]
    count = user_query.count()
    return RestResponse.success_list(count=count, data=list(query))


@log_func
def user_simple_list(request: HttpRequest):
    user = request.session.get('user')
    if user is not None and user.get('username') is not None \
            and user.get('username') == 'admin':
        res_list = User.objects.values('id', 'username', 'name')
        return RestResponse.success(data=list(res_list))

    res_list = User.objects.filter(is_admin=False) \
        .values('id', 'username', 'name')
    return RestResponse.success(data=list(res_list))


@log_func
@api_op_user
@op_admin
def user_add(request: HttpRequest):
    body = utils.request_body(request)
    username = body.get("username", "")
    password = body.get('password', '')
    name = body.get('name', '')
    role = body.get('role', 2)
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
    bind_dispatch = body.get("bind_dispatch")
    if utils.str_is_null(bind_dispatch):
        return RestResponse.failure("参数错误，缺少禁用参数")

    bind_dispatch = str(bind_dispatch) == 'on'

    back_type = body.get('back_type')
    if utils.str_is_null(back_type) or not utils.is_int(back_type):
        return RestResponse.failure("参数错误，后台类型必须是一个数值")

    back_type = int(back_type)
    logging.info("addUser#back_type = %s", back_type)
    if back_type not in (USER_BACK_TYPE_NONE, USER_BACK_TYPE_LINE, USER_BACK_TYPE_WA):
        return RestResponse.failure("参数错误，后台类型选择错误，未知类型:" + str(back_type))

    create_user = User.objects.create(
        username=username, password=password, name=name, role=role,
        bind_dispatch=bind_dispatch, back_type=back_type,
        create_time=time_utils.get_now_bj_time_str(),
        update_time=time_utils.get_now_bj_time_str()
    )
    create_user.password = ''
    return RestResponse.success(data=utils.object_to_json(create_user))


@log_func
@api_op_user
@op_admin
def user_update(request: HttpRequest):
    body = utils.request_body(request)
    logging.info("修改用户#body = %s", body)
    u_id = body.get("id", "")
    if not str(u_id).isdigit() and int(u_id) <= 0:
        return RestResponse.failure("参数错误，需要username或id")

    name = body.get('name', '')
    role = body.get('role')

    if role is None or not utils.is_int(role):
        return RestResponse.failure("更新失败，角色信息不能为空")

    bind_dispatch = body.get("bind_dispatch")
    if utils.str_is_null(bind_dispatch):
        return RestResponse.failure("参数错误，缺少禁用参数")

    bind_dispatch = str(bind_dispatch) == 'on'

    upd_dict = {
        'name': name,
        'role': role,
        'bind_dispatch': bind_dispatch,
        'update_time': time_utils.get_now_bj_time_str()
    }

    back_type = body.get('back_type')
    if not utils.str_is_null(back_type):
        if not utils.is_int(back_type):
            return RestResponse.failure("参数错误，后台类型必须是一个数值")

        back_type = int(back_type)
        logging.info("updateUser#back_type = %s", back_type)
        if back_type not in (USER_BACK_TYPE_NONE, USER_BACK_TYPE_LINE, USER_BACK_TYPE_WA):
            return RestResponse.failure("参数错误，后台类型选择错误，未知类型:" + str(back_type))

        upd_dict['back_type'] = back_type
    query = User.objects.filter(id=u_id)
    if not query.exists():
        return RestResponse.failure("更新失败，用户记录不存在")
    rows = query.update(**upd_dict)
    return RestResponse.success(data={
        'rows': rows
    })


@log_func
@api_op_user
@op_admin
def user_del(request: HttpRequest):
    body = utils.request_body(request)
    u_id = body.get("id", "")
    username = body.get("username", "")
    if utils.str_is_null(username) or (not str(u_id).isdigit() and int(u_id) <= 0):
        return RestResponse.failure("参数错误，需要username或id")
    q = Q(id=u_id) | Q(username=username)
    query = User.objects.filter(q)
    if not query.exists():
        return RestResponse.failure("删除失败，记录不存在")

    if query.filter(is_admin=True).exists():
        return RestResponse.failure("删除失败，无法删除管理员")

    deleted, del_count = query.delete()
    return RestResponse.success(data={
        'deleted': deleted,
        'delete_count': del_count
    })


@log_func
@api_op_user
@op_admin
def user_bind_dispatch(request: HttpRequest):
    """
    禁用用户分配
    """
    body = utils.request_body(request)
    u_id = body.get("id", "")
    bind_dispatch = body.get("bind_dispatch")
    if not str(u_id).isdigit() and int(u_id) <= 0:
        return RestResponse.failure("参数错误，需要用户id")

    if utils.str_is_null(bind_dispatch):
        return RestResponse.failure("参数错误，需要禁用参数")

    bind_dispatch = utils.is_bool_val(bind_dispatch)
    query = User.objects.filter(id=u_id)
    if not query.exists():
        return RestResponse.failure("修改失败，用户 " + u_id + " 不存在")

    query.update(bind_dispatch=bind_dispatch, update_time=time_utils.get_now_bj_time_str())

    return RestResponse.success("禁用成功" if bind_dispatch else "解除禁用成功")


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
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="' + escape_uri_path(file_name) + '"'
    return response
