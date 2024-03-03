from util.restful import RestResponse


class CommonException(Exception):
    """公共异常类"""

    def __init__(self, code: int, msg: str):
        self.code = code
        self.errmsg = msg
        super().__init__()


class BusinessException(CommonException):
    """业务异常类"""

    @classmethod
    def msg(cls, msg: str):
        return BusinessException(-1, msg)


class APIException(CommonException):
    """接口异常类"""
    pass
