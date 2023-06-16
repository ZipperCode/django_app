import logging
import os
import uuid
from pathlib import Path

from django.http import HttpRequest, HttpResponse

from util import utils
from util.restful import RestResponse
from util.utils import handle_uploaded_file
from web_app.dao import account_dao
from web_app.decorators.admin_decorator import log_func, api_op_user, op_admin
from web_app.decorators.restful_decorator import api_post
from web_app.forms.upload_form import UploadFileForm
from web_app.model.accounts import AccountId, AccountQr
from web_app.model.users import User
from web_app.settings import BASE_DIR

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TEMP_DIR = os.path.join(BASE_DIR, "data", 'temp')


@log_func
@api_op_user
def account_id_list(request: HttpRequest):
    user_id = request.session.get('user_id')
    if not id or utils.str_is_null(user_id):
        return RestResponse.failure("获取信息失败，用户未登录")

    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)
    res, count = account_dao.search_account_qr_page(body, start_row, end_row, int(user_id))
    return RestResponse.success_list(count=count, data=res)


def account_qr_add(request: HttpRequest):
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


@api_post
@api_op_user
def account_qr_update(request: HttpRequest):
    body = utils.request_body(request)
    db_id = body.get('id', "")
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")
    if utils.str_is_null(db_id) or utils.is_int(db_id):
        return RestResponse.failure("修改失败，id不能为空或只能数字")

    user_id = request.session.get('user_id')
    if not id or utils.str_is_null(user_id):
        return RestResponse.failure("修改失败，未获取到登录用户信息")

    query = AccountQr.objects.filter(id=db_id)
    if not query.exists():
        return RestResponse.failure("修改失败，记录不存在")

    query.update(
        country=country, age=age, work=work, money=money, mark=mark
    )

    return RestResponse.success("更新成功")


@log_func
@op_admin
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


@log_func
@api_op_user
def account_qr_upload(request: HttpRequest):
    f = request.FILES["file"]
    filename = request.POST["filename"]
    if not f:
        return HttpResponse("上传失败，数据传输异常")

    user_id = request.session.get('user_id')
    if not id or utils.str_is_null(user_id):
        return RestResponse.failure("上传失败，未获取到登录用户信息")

    logging.info("account_qr_upload# f = %s", f)
    logging.info("account_qr_upload#name = %s", filename)
    ext = str(os.path.splitext(filename)[-1])
    logging.info("account_qr_upload#ext = %s", ext)
    new_file_name = str(uuid.uuid1()) + ext
    temp_path = os.path.join(TEMP_DIR, new_file_name)
    logging.info("account_id_batch_upload#new_file_name = %s", ext)
    temp_path = os.path.join(TEMP_DIR, new_file_name)
    path = handle_uploaded_file(temp_path, f)
    if not path:
        return RestResponse.failure("上传失败，保存临时文件失败")

    # 识别图片

