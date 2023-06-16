import logging

from django.http import HttpResponseRedirect, HttpRequest, HttpResponse
from django.shortcuts import render

from util.restful import RestResponse
from web_app import views

try:
    from django.utils.deprecation import MiddlewareMixin  # Django 1.10.x
except ImportError:
    MiddlewareMixin = object

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class LoginMiddleware(MiddlewareMixin):
    def process_request(self, request: HttpRequest):
        # logging.info("login拦截器，request => path = %s", str(request.path))
        user = {
            'username': 'admin',
            'name': 'admin',
            'is_admin': True
        }
        request.session['user'] = user

        u = request.session.get('user')
        if u is not None:
            if u.get('id') is not None and u.get('username') is not None:
                request.session['user_id'] = u.get("id")
                request.session['username'] = u.get('username')

        return None

    def process_response(self, request, response: HttpResponse):
        # logging.info("login拦截器，response => status_code = %s", response.status_code)
        # if response.status_code == 404:
        #     return render(request, "static/404.html")
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        p = str(request.path)
        logging.info("login拦截器，view => path = %s", p)
        # 非登录接口，且需要跳转到授权接口
        # if p.find("/view/login") == -1 and p.find("/view/auth/") != -1:
        #     if not request.session.get('user', None):
        #         return views.login_view(request)

        return view_func(request)

    def process_exception(self, request, exception):
        logging.info("拦截器, exception => ")
        return RestResponse.failure("发生错误, " + str(exception))


    def process_template_response(self, request):
        logging.info("login拦截器, template => 404")
        return render(request, "static/404.html")
