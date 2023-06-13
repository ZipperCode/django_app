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
from web_app.restfuls import user_restful

urlpatterns = [
    path('.', views.login_view),
    path('view/auth/index', views.index_view),
    path('view/auth/console.html', views.console_view),
    path('view/auth/user/modify_pwd', views.modify_pwd),

    path('view/login', views.login_view),
    path('404.html', views.not_found_view),


    path('api/login', user_restful.login),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
