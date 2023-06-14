import logging
from django.http import HttpRequest
from django.shortcuts import render
from django.utils.crypto import md5

from web_app.decorators.admin_decorator import log_func
from web_app.model.users import User

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

UNKNOWN_KEY = "unknown_info"
UNKNOWN_REMARK = "未知数据"

if not User.objects.filter(username='admin').exists():
    User.objects.create(username='admin', password=md5("admin".encode()).digest().hex(), is_admin=True, name="Admin")


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


@log_func
def index_view(request: HttpRequest):
    return render(request, 'index.html')


@log_func
def login_view(request: HttpRequest):
    return render(request, 'login.html')


@log_func
def logout(request):
    context = {
        "msg": "注销成功"
    }
    request.session.flush()
    return render(request, 'login.html', context)


@log_func
def not_found_view(request: HttpRequest):
    return render(request, 'static/404.html')


@log_func
def console_view(request: HttpRequest):
    return render(request, 'console.html')


@log_func
def modify_pwd(request: HttpRequest):
    return render(request, 'modify_pwd.html')


@log_func
def setting_view(request: HttpRequest):
    return render(request, 'setting.html')


@log_func
def user_list_view(request: HttpRequest):
    return render(request, 'user/user.html')


@log_func
def user_add_view(request: HttpRequest):
    return render(request, 'user/user_add.html')


@log_func
def user_edit_view(request: HttpRequest):
    return render(request, 'user/user_edit.html')


@log_func
def account_id_list_view(request: HttpRequest):
    return render(request, 'account/id_list.html')


@log_func
def account_qr_list_view(request: HttpRequest):
    return render(request, 'account/qr_list.html')
