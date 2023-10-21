import functools
import logging

from django.http import HttpRequest

from util import utils
from util.restful import RestResponse
from web_app.model.users import User

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def log_func(func):
    """
    打印方法名称装饰器
    """

    @functools.wraps(func)
    def wrapper(*args, **kw):
        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>> {func.__name__} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        if args is not None and len(args) > 0:
            request = args[0]
            if isinstance(request, HttpRequest):
                body = utils.request_body(request)
                back_type = body.get("back_type", -1)
                logging.info("back_type = %s", back_type)
                logging.info("body = %s", body)
        return func(*args, **kw)

    return wrapper


def op_admin(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        request = args[0]
        if isinstance(request, HttpRequest):
            logging.debug(f"admin 权限拦截器, 处理函数 {func.__name__}")
            user = request.session.get('user')
            if user is None or user.get('role') != 0:
                return RestResponse.failure("非管理员无法操作")

        return func(*args, **kw)

    return wrapper


def api_op_user(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        request = args[0]
        if isinstance(request, HttpRequest):
            logging.debug(f"用户操作 拦截器, 处理函数 {func.__name__}")
            user = request.session.get('user')
            if user is None or not user.get('username'):
                return RestResponse.failure("未登录，无法操作")

            username = user.get('username')
            logging.info("用户操作 拦截器 # username = %s", username)
            query = User.objects.filter(username=username)
            if not query.exists():
                return RestResponse.failure("用户不存在，无法操作")

            request.session['user_id'] = query.first().id

        return func(*args, **kw)

    return wrapper
