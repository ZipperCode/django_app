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

from web_app import views, settings
from web_app.restfuls import user_restful, account_restful

urlpatterns = [
    path('.', views.login_view),
    path('view/auth/index', views.index_view),
    path('view/auth/console.html', views.console_view),
    path('view/auth/user/modify_pwd', views.modify_pwd),
    path('view/auth/setting.html', views.setting_view),
    path('view/auth/user_view', views.user_list_view),
    path('view/auth/user_add_view', views.user_add_view),
    path('view/auth/user_edit_view', views.user_edit_view),
    path('view/auth/account_id/list', views.account_id_list_view),

    path('view/auth/account_qr/list', views.account_qr_list_view),


    path('view/login', views.login_view),
    path('logout', views.logout),
    path('404.html', views.not_found_view),


    path('api/login', user_restful.login),
    path('api/modify_pwd', user_restful.modify_password),
    path('api/user_list', user_restful.user_list),
    path('api/user_simple_list', user_restful.user_simple_list),
    path('api/user_add', user_restful.user_add),
    path('api/user_update', user_restful.user_add),
    path('api/account_id/list', account_restful.account_id_list),
    path('api/account_id/add', account_restful.account_id_add),
    path('api/account_id/update', account_restful.account_id_update),
    path('api/account_id/del', account_restful.account_id_del),
    path('api/account_id/upload', account_restful.account_id_upload),
    path('api/account_id/bat_upload', account_restful.account_id_batch_upload),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
