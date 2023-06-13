import logging
from django.http import HttpRequest
from django.shortcuts import render

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
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
    return render(request, 'index1.html', context)


def index_view(request: HttpRequest):
    logging.info("render index1.html")
    return render(request, 'index.html')


def login_view(request: HttpRequest):
    logging.info("render login.html")
    return render(request, 'login.html')


def not_found_view(request: HttpRequest):
    logging.info("render not_found_view.html")
    return render(request, 'static/404.html')


def console_view(request: HttpRequest):
    logging.info("render console_view.html")
    return render(request, 'console.html')


def modify_pwd(request: HttpRequest):
    logging.info("render modify_pwd.html")
    return render(request, 'modify_pwd.html')
