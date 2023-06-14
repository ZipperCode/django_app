import logging
import os
import uuid
from pathlib import Path

from django.http import HttpRequest

from util import utils
from util.restful import RestResponse
from util.utils import handle_uploaded_file
from web_app.decorators.admin_decorator import log_func
from web_app.forms.upload_form import UploadFileForm
from web_app.model.accounts import AccountId, AccountQr
from web_app.model.users import User
from web_app.settings import BASE_DIR

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TEMP_DIR = os.path.join(BASE_DIR, "data", 'temp')


def account_qr_add(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    # TODO 二维码
    qr = request.FILES['qr_file']
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")

    user = request.session.get('user')
    logging.info("account_id_upload#user = %s", user.username)
    if not User.objects.filter(username=user.username).exists():
        return RestResponse.failure("添加失败，操作用户不存在")

    qr_content = "content"
    if utils.str_is_null(qr_content):
        return RestResponse.failure("添加失败，解析二维码失败")

    AccountQr.objects.create(
        qr_content=qr_content, qr_path=qr, country=country, age=age,
        work=work, money=money, mark=mark,
        op_user_id=user.id
    )

    return RestResponse.success("添加成功")


def account_qr_update(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    id_ = body.get('id', "")
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")
    if utils.str_is_null(id_) or utils.is_int(id_):
        return RestResponse.failure("修改失败，id不能为空或只能数字")

    user = request.session.get('user')
    logging.info("account_id_upload#user = %s", user.username)
    if not User.objects.filter(username=user.username).exists():
        return RestResponse.failure("修改失败，操作用户不存在")

    query = AccountQr.objects.filter(id=id_)
    if not query.exists():
        return RestResponse.failure("修改失败，记录不存在")

    query.update(
        country=country, age=age,
        work=work, money=money, mark=mark,
        op_user_id=user.id
    )

    return RestResponse.success("更新成功")


@log_func
def account_qr_del(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    id_ = body.get('id', "")
    logging.info("account_qr_del#id_ = %s", id_)
    if utils.str_is_null(id_) or utils.is_int(id_):
        return RestResponse.failure("删除失败，id不能为空或只能数字")

    AccountQr.objects.filter(id=id_).delete()
    return RestResponse.failure("删除成功")

