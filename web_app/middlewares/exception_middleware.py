import logging

from django.utils.deprecation import MiddlewareMixin
from util.exception import CommonException
from util.restful import RestResponse

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class ExceptionMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):
        exception_class = exception.__class__
        logging.info("异常拦截, exception => %s %s",str(exception_class), exception)
        if isinstance(exception, CommonException):
            # 业务异常处理
            return RestResponse({
                'code': exception.code,
                'msg': exception.errmsg
            })
        raise exception
        # return RestResponse.failure("发生错误, " + str(exception))
