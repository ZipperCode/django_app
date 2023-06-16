import functools
import logging

from django.http import HttpRequest

from util.restful import RestResponse

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def api_post(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        request = args[0]
        if isinstance(request, HttpRequest):
            if request.method != "POST":
                return RestResponse.failure("must use post")

        return func(*args, **kw)

    return wrapper

