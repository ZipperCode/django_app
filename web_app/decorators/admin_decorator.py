import functools
import logging

from django.http import HttpRequest

from util.restful import RestResponse

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
        return func(*args, **kw)

    return wrapper


def op_admin():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            request = args[0]
            if isinstance(request, HttpRequest):
                logging.debug(f"admin 权限拦截器, 处理函数 {func.__name__}")
                user = request.session.get('user')
                if user is None or not user.is_admin:
                    return RestResponse.failure("非管理员无法操作")

            return func(*args, **kw)

        return wrapper

    return decorator
