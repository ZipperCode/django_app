import datetime
import logging
import os
import platform
import time
import traceback

import psutil
from django.http import HttpRequest
from django.shortcuts import render
from django.utils.crypto import md5

from util import time_utils
from web_app.decorators.admin_decorator import log_func
from web_app.model.users import User, USER_ROLE_ADMIN, USER_ROLE_UPLOADER, USER_ROLE_BUSINESS
from web_app.util.wa_map import MENU_MAP

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


@log_func
def index_view(request: HttpRequest):
    user = request.session.get('user')
    context = {}
    if user.get('role') != 0:
        back_type = user.get('back_type')
        wa_menu_list = []
        # menu_list = UserMenu.objects.filter(user_id=user.id).all()
        # if len(menu_list) > 0:
        #     menu_types = map(lambda x: x.menu_type, menu_list)
        #     for menu_type in menu_types:
        #         d = MENU_MAP.get(menu_type)
        #         if d:
        #             wa_menu_list.append(d)
        wa_dict = MENU_MAP.get(back_type)
        if wa_dict:
            wa_menu_list.append(wa_dict)
        context['wa_menu_list'] = wa_menu_list

    else:
        context['wa_menu_list'] = list(MENU_MAP.values())

    return render(request, 'index.html', context)


@log_func
def login_view(request: HttpRequest):
    try:
        if not User.objects.filter(username='admin').exists():
            User.objects.create(
                username='admin',
                password=md5("admin".encode()).digest().hex().lower(),
                is_admin=True,
                name="Admin",
                role=USER_ROLE_ADMIN
            )
    except BaseException:
        logging.info("append excel fail = %s", traceback.format_exc())
        pass

    if request.session.get('user') is not None:
        context = {}
        user = request.session.get('user')
        if user.get('role') != 0:
            back_type = user.get('back_type')
            wa_menu_list = []
            # menu_list = UserMenu.objects.filter(user_id=user.id).all()
            # if len(menu_list) > 0:
            #     menu_types = map(lambda x: x.menu_type, menu_list)
            #     for menu_type in menu_types:
            #         d = MENU_MAP.get(menu_type)
            #         if d:
            #             wa_menu_list.append(d)
            wa_dict = MENU_MAP.get(back_type)
            if wa_dict:
                wa_menu_list.append(wa_dict)
            context['wa_menu_list'] = wa_menu_list

        else:
            context['wa_menu_list'] = list(MENU_MAP.values())
        return render(request, 'index.html', context)

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
    # # 硬件信息
    context = {}
    context['host'] = request.get_host()
    context['port'] = request.get_port()

    # 系统
    try:
        # linux
        system_info = os.uname()
        system = system_info.sysname
        node = system_info.nodename
        version = system_info.version
    except Exception:
        # windows
        system_info = platform.uname()
        system = system_info.system
        node = system_info.system
        version = system_info.version
    system_machine = platform.machine()  # 获取操作系统架构
    cpu_count = psutil.cpu_count()  # cpu核数

    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    now_time = datetime.datetime.fromtimestamp(time.time())
    boot_delta = now_time - boot_time

    context['system_machine'] = system_machine
    context['system'] = system
    context['node'] = node
    context['version'] = version
    context['cpu_count'] = cpu_count
    context['boot_time'] = time_utils.fmt_datetime(boot_time)
    context['now_time'] = time_utils.fmt_datetime(now_time)
    context['boot_delta'] = boot_delta

    # 内存
    svmem = psutil.virtual_memory()
    mem_total = svmem.total  # 系统内存总数
    mem_used = svmem.used  # 内存已使用
    mem_free = svmem.free  # 内存空闲大小
    mem_per = svmem.percent  # 内存使用率

    context['mem_total'] = round(mem_total / 1024 / 1024, 2)
    context['mem_used'] = round(mem_used / 1024 / 1024, 2)
    context['mem_free'] = round(mem_free / 1024 / 1024, 2)
    context['mem_per'] = mem_per

    return render(request, 'console.html', context)


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
    logging.info(request)
    user = request.session['user']
    if user is None:
        return render(request, 'login.html', {
            "msg": "请先登录"
        })

    if user.get('role') == USER_ROLE_ADMIN:
        return render(request, 'account/line_id_list.html')
    elif user.get("role") == USER_ROLE_UPLOADER:
        return render(request, 'account/line_id_uploader_list.html')
    elif user.get('role') == USER_ROLE_BUSINESS:
        return render(request, 'account/line_id_business_list.html')
    return render(request, 'login.html', {
        "msg": "请先登录"
    })

@log_func
def lid_list_view(request: HttpRequest):
    logging.info(request)
    user = request.session['user']
    if user is None:
        return render(request, 'login.html', {
            "msg": "请先登录"
        })
    classify = request.GET['line_classify']
    context = {
        "classify": classify
    }

    if user.get('role') == USER_ROLE_ADMIN:
        return render(request, 'line/line_id_list.html', context)
    elif user.get("role") == USER_ROLE_UPLOADER:
        return render(request, 'line/line_id_uploader_list.html', context)
    elif user.get('role') == USER_ROLE_BUSINESS:
        return render(request, 'line/line_id_business_list.html', context)
    return render(request, 'login.html', {
        "msg": "请先登录"
    })


@log_func
def account_qr_list_view(request: HttpRequest):
    user = request.session['user']
    if user is None:
        return render(request, 'login.html', {
            "msg": "请先登录"
        })

    if user.get('role') == USER_ROLE_ADMIN:
        return render(request, 'account/line_qr_list.html')
    elif user.get("role") == USER_ROLE_UPLOADER:
        return render(request, 'account/line_qr_uploader_list.html')
    elif user.get('role') == USER_ROLE_BUSINESS:
        return render(request, 'account/line_qr_business_list.html')
    return render(request, 'login.html', {
        "msg": "请先登录"
    })

@log_func
def lqr_list_view(request:HttpRequest):
    user = request.session['user']
    if user is None:
        return render(request, 'login.html', {
            "msg": "请先登录"
        })
    classify=None
    try:
        classify = request.GET['classify']
    except:
        classify = request.GET['line_classify']
        pass
    context = {
        "classify": classify
    }
    if user.get('role') == USER_ROLE_ADMIN:
        return render(request, 'line/line_qr_list.html', context)
    elif user.get("role") == USER_ROLE_UPLOADER:
        return render(request, 'line/line_qr_uploader_list.html', context)
    elif user.get('role') == USER_ROLE_BUSINESS:
        return render(request, 'line/line_qr_business_list.html', context)
    return render(request, 'login.html', {
        "msg": "请先登录"
    })


@log_func
def lines_aid_record_list_view(request):
    return render(request, 'account/line_id_record_list.html')


@log_func
def lines_qr_record_list_view(request):
    return render(request, 'account/line_qr_record_list.html')


@log_func
def lid_record_list_view(request):
    classify=None
    try:
        classify = request.GET['classify']
    except:
        classify = request.GET['line_classify']
        pass
    context = {
        "classify": classify
    }
    return render(request, 'line/line_id_record_list.html', context)


@log_func
def lqr_record_list_view(request):
    classify=None
    try:
        classify = request.GET['classify']
    except:
        classify = request.GET['line_classify']
        pass
    context = {
        "classify": classify
    }
    return render(request, 'line/line_qr_record_list.html', context)


"""
############################################ WhatsApp ##################################################
"""


@log_func
def whatsapp_account_id_list_view(request: HttpRequest):
    logging.info(request)
    user = request.session['user']
    if user is None:
        return render(request, 'login.html', {
            "msg": "请先登录"
        })

    if user.get('role') == USER_ROLE_ADMIN:
        return render(request, 'account/wa_id_list.html')
    elif user.get("role") == USER_ROLE_UPLOADER:
        return render(request, 'account/wa_id_uploader_list.html')
    elif user.get('role') == USER_ROLE_BUSINESS:
        return render(request, 'account/wa_id_business_list.html')
    return render(request, 'login.html', {
        "msg": "请先登录"
    })


@log_func
def whatsapp_account_qr_list_view(request: HttpRequest):
    user = request.session['user']
    if user is None:
        return render(request, 'login.html', {
            "msg": "请先登录"
        })

    if user.get('role') == USER_ROLE_ADMIN:
        return render(request, 'account/wa_qr_list.html')
    elif user.get("role") == USER_ROLE_UPLOADER:
        return render(request, 'account/wa_qr_uploader_list.html')
    elif user.get('role') == USER_ROLE_BUSINESS:
        return render(request, 'account/wa_qr_business_list.html')
    return render(request, 'login.html', {
        "msg": "请先登录"
    })


@log_func
def whatsapp_aid_record_list_view(request):
    return render(request, 'account/wa_id_record_list.html')


@log_func
def whatsapp_qr_record_list_view(request):
    return render(request, 'account/wa_qr_record_list.html')


"""
========================================== whatsapp2 ==================================
"""


@log_func
def whatsapp2_account_id_list_view(request: HttpRequest):
    logging.info(request)
    user = request.session['user']
    if user is None:
        return render(request, 'login.html', {
            "msg": "请先登录"
        })

    if user.get('role') == USER_ROLE_ADMIN:
        return render(request, 'account/wa2_id_list.html')
    elif user.get("role") == USER_ROLE_UPLOADER:
        return render(request, 'account/wa2_id_uploader_list.html')
    elif user.get('role') == USER_ROLE_BUSINESS:
        return render(request, 'account/wa2_id_business_list.html')
    return render(request, 'login.html', {
        "msg": "请先登录"
    })


@log_func
def whatsapp2_account_qr_list_view(request: HttpRequest):
    user = request.session['user']
    if user is None:
        return render(request, 'login.html', {
            "msg": "请先登录"
        })

    if user.get('role') == USER_ROLE_ADMIN:
        return render(request, 'account/wa2_qr_list.html')
    elif user.get("role") == USER_ROLE_UPLOADER:
        return render(request, 'account/wa2_qr_uploader_list.html')
    elif user.get('role') == USER_ROLE_BUSINESS:
        return render(request, 'account/wa2_qr_business_list.html')
    return render(request, 'login.html', {
        "msg": "请先登录"
    })


@log_func
def whatsapp2_aid_record_list_view(request):
    return render(request, 'account/wa2_id_record_list.html')


@log_func
def whatsapp2_qr_record_list_view(request):
    return render(request, 'account/wa2_qr_record_list.html')


"""
========================================== whatsapp common ==================================
"""


@log_func
def wa_account_id_list_view(request: HttpRequest):
    logging.info(request)
    user = request.session['user']
    if user is None:
        return render(request, 'login.html', {
            "msg": "请先登录"
        })

    back_type = request.GET['back_type'] or user.get('back_type')
    context = {
        "back_type": back_type
    }
    if user.get('role') == USER_ROLE_ADMIN:
        return render(request, 'whatsapp/wa_id_list.html', context)
    elif user.get("role") == USER_ROLE_UPLOADER:
        return render(request, 'whatsapp/wa_id_uploader_list.html', context)
    elif user.get('role') == USER_ROLE_BUSINESS:
        return render(request, 'whatsapp/wa_id_business_list.html', context)
    return render(request, 'login.html', {
        "msg": "请先登录"
    })


@log_func
def wa_account_qr_list_view(request: HttpRequest):
    user = request.session['user']
    if user is None:
        return render(request, 'login.html', {
            "msg": "请先登录"
        })
    back_type = request.GET['back_type'] or user.get('back_type')
    context = {
        "back_type": back_type
    }
    if user.get('role') == USER_ROLE_ADMIN:
        return render(request, 'whatsapp/wa_qr_list.html', context)
    elif user.get("role") == USER_ROLE_UPLOADER:
        return render(request, 'whatsapp/wa_qr_uploader_list.html', context)
    elif user.get('role') == USER_ROLE_BUSINESS:
        return render(request, 'whatsapp/wa_qr_business_list.html', context)
    return render(request, 'login.html', {
        "msg": "请先登录"
    })


@log_func
def wa_aid_record_list_view(request):
    back_type = request.GET.get('back_type')
    context = {
        "back_type": back_type
    }
    return render(request, 'whatsapp/wa_id_record_list.html', context)


@log_func
def wa_qr_record_list_view(request):
    back_type = request.GET.get('back_type')
    context = {
        "back_type": back_type
    }
    return render(request, 'whatsapp/wa_qr_record_list.html', context)
