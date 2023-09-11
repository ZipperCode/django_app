"""web_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve

from web_app import views, settings
from web_app.restfuls import user_restful, account_restful, account_qr_restful, wa_id_restful, wa_qr_restful, \
    wa_id_restful2, wa_qr_restful2

urlpatterns = [
    path('', views.login_view),
    path('view/auth/index', views.index_view),
    path('view/auth/console.html', views.console_view),
    path('view/auth/user/modify_pwd', views.modify_pwd),
    path('view/auth/setting.html', views.setting_view),
    path('view/auth/user_view', views.user_list_view),
    path('view/auth/user_add_view', views.user_add_view),
    path('view/auth/user_edit_view', views.user_edit_view),
    path('view/auth/account_id/list', views.account_id_list_view),
    path('view/auth/account_qr/list', views.account_qr_list_view),
    # line 分配记录
    path('view/auth/aid_record/list', views.lines_aid_record_list_view),
    path('view/auth/qr_record/list', views.lines_qr_record_list_view),
    # Whatsapp
    path('view/auth/whatsapp/account_id/list', views.whatsapp_account_id_list_view),
    path('view/auth/whatsapp/account_qr/list', views.whatsapp_account_qr_list_view),
    path('view/auth/whatsapp/aid_record/list', views.whatsapp_aid_record_list_view),
    path('view/auth/whatsapp/qr_record/list', views.whatsapp_qr_record_list_view),
    # whatsapp2
    path('view/auth/whatsapp2/account_id/list', views.whatsapp2_account_id_list_view),
    path('view/auth/whatsapp2/account_qr/list', views.whatsapp2_account_qr_list_view),
    path('view/auth/whatsapp2/aid_record/list', views.whatsapp2_aid_record_list_view),
    path('view/auth/whatsapp2/qr_record/list', views.whatsapp2_qr_record_list_view),

    path('view/login', views.login_view),
    path('logout', views.logout),
    path('404.html', views.not_found_view),


    path('api/login', user_restful.login),
    path('api/modify_pwd', user_restful.modify_password),
    path('api/admin/modify_pwd', user_restful.modify_password_admin),
    path('api/user_list', user_restful.user_list),
    path('api/user_simple_list', user_restful.user_simple_list),
    path('api/user_add', user_restful.user_add),
    path('api/user_update', user_restful.user_update),
    path('api/user_del', user_restful.user_del),
    path('api/user/bind_dispatch', user_restful.user_bind_dispatch),

    path('api/account_id/list', account_restful.account_id_list),
    path('api/account_id/business_list', account_restful.account_id_business_list),
    path('api/account_id/add', account_restful.account_id_add),
    path('api/account_id/update', account_restful.account_id_update),
    path('api/account_id/del', account_restful.account_id_del),
    path('api/account_id/upload', account_restful.account_id_upload),
    path('api/account_id/bat_upload', account_restful.account_id_batch_upload),
    path('api/account_id/export', account_restful.account_id_export),
    path('api/account_id/dispatcher', account_restful.handle_dispatcher),

    path('api/account_qr/list', account_qr_restful.account_qr_list),
    path('api/account_qr/business_list', account_qr_restful.business_list),
    path('api/account_qr/upload', account_qr_restful.account_qr_upload),
    path('api/account_qr/bat_upload', account_qr_restful.account_qr_batch_upload),
    path('api/account_qr/update', account_qr_restful.account_qr_update),
    path('api/account_qr/del', account_qr_restful.account_qr_del),
    path('api/account_qr/export_select', account_qr_restful.account_qr_export_with_id),
    path('api/account_qr/export', account_qr_restful.account_qr_export),
    path('api/account_qr/dispatcher', account_qr_restful.handle_dispatcher),

    # 分配记录
    path('api/lines/aid_record/list', account_restful.dispatch_record_list),
    path('api/lines/qr_record/list', account_qr_restful.dispatch_record_list),

    # whatsApp ID
    path('api/wa/account_id/list', wa_id_restful.account_id_list),
    path('api/wa/account_id/business_list', wa_id_restful.account_id_business_list),
    path('api/wa/account_id/add', wa_id_restful.account_id_add),
    path('api/wa/account_id/update', wa_id_restful.account_id_update),
    path('api/wa/account_id/del', wa_id_restful.account_id_del),
    path('api/wa/account_id/upload', wa_id_restful.account_id_upload),
    path('api/wa/account_id/bat_upload', wa_id_restful.account_id_batch_upload),
    path('api/wa/account_id/export', wa_id_restful.account_id_export),
    path('api/wa/account_id/dispatcher', wa_id_restful.handle_dispatcher),
    path('api/wa/aid_record/list', wa_id_restful.dispatch_record_list),
    # WhatsApp Qr
    path('api/wa/account_qr/list', wa_qr_restful.account_qr_list),
    path('api/wa/account_qr/business_list', wa_qr_restful.business_list),
    path('api/wa/account_qr/upload', wa_qr_restful.account_qr_upload),
    path('api/wa/account_qr/bat_upload', wa_qr_restful.account_qr_batch_upload),
    path('api/wa/account_qr/update', wa_qr_restful.account_qr_update),
    path('api/wa/account_qr/del', wa_qr_restful.account_qr_del),
    path('api/wa/account_qr/export_select', wa_qr_restful.account_qr_export_with_id),
    path('api/wa/account_qr/export', wa_qr_restful.account_qr_export),
    path('api/wa/account_qr/dispatcher', wa_qr_restful.handle_dispatcher),
    path('api/wa/qr_record/list', wa_qr_restful.dispatch_record_list),
    # wa2
    path('api/wa2/account_id/list', wa_id_restful2.wa2_account_id_list),
    path('api/wa2/account_id/business_list', wa_id_restful2.wa2_account_id_business_list),
    path('api/wa2/account_id/add', wa_id_restful2.wa2_account_id_add),
    path('api/wa2/account_id/update', wa_id_restful2.wa2_account_id_update),
    path('api/wa2/account_id/del', wa_id_restful2.wa2_account_id_del),
    path('api/wa2/account_id/upload', wa_id_restful2.wa2_account_id_upload),
    path('api/wa2/account_id/bat_upload', wa_id_restful2.wa2_account_id_batch_upload),
    path('api/wa2/account_id/export', wa_id_restful2.wa2_account_id_export),
    path('api/wa2/account_id/dispatcher', wa_id_restful2.wa2_handle_dispatcher),
    path('api/wa2/aid_record/list', wa_id_restful2.wa2_dispatch_record_list),
    # WhatsApp Qr
    path('api/wa2/account_qr/list', wa_qr_restful2.wa2_account_qr_list),
    path('api/wa2/account_qr/business_list', wa_qr_restful2.wa2_business_list),
    path('api/wa2/account_qr/upload', wa_qr_restful2.wa2_account_qr_upload),
    path('api/wa2/account_qr/bat_upload', wa_qr_restful2.wa2_account_qr_batch_upload),
    path('api/wa2/account_qr/update', wa_qr_restful2.wa2_account_qr_update),
    path('api/wa2/account_qr/del', wa_qr_restful2.wa2_account_qr_del),
    path('api/wa2/account_qr/export_select', wa_qr_restful2.wa2_account_qr_export_with_id),
    path('api/wa2/account_qr/export', wa_qr_restful2.wa2_account_qr_export),
    path('api/wa2/account_qr/dispatcher', wa_qr_restful2.wa2_handle_dispatcher),
    path('api/wa2/qr_record/list', wa_qr_restful2.wa2_dispatch_record_list),

    re_path(r'media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})
] + static(settings.MEDIA_URL, serve, document_root=settings.MEDIA_ROOT)
