import logging
import os
import uuid
from pathlib import Path

from django.db.models import Q
from django.http import HttpRequest

from util import utils
from util.restful import RestResponse
from util.utils import handle_uploaded_file
from web_app.dao import account_dao
from web_app.decorators.admin_decorator import log_func
from web_app.model.accounts import AccountId
from web_app.model.users import User
from web_app.settings import BASE_DIR

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TEMP_DIR = os.path.join(BASE_DIR, "data", 'temp')


@log_func
def account_id_list(request: HttpRequest):
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)
    res, count = account_dao.search_account_id_page(body, start_row, end_row)
    return RestResponse.success_list(count=count, data=res)


def account_id_add(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    a_id = body.get("a_id", "")
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")

    user = request.session.get('user')
    logging.info("account_id_upload#user = %s", user.username)
    if not User.objects.filter(username=user.username).exists():
        return RestResponse.failure("添加失败，操作用户不存在")

    if utils.str_is_null(a_id):
        return RestResponse.failure("添加失败，a_id不能为空")

    if AccountId.objects.filter(account_id=a_id).exists():
        return RestResponse.failure("添加失败，该id已经存在")

    AccountId.objects.create(
        account_id=a_id, country=country, age=age,
        work=work, money=money, mark=mark,
        op_user_id=user.id
    )

    return RestResponse.success("添加成功")


def account_id_update(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    a_id = body.get("a_id", "")
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")

    user = request.session.get('user')
    logging.info("account_id_upload#user = %s", user.username)
    if not User.objects.filter(username=user.username).exists():
        return RestResponse.failure("修改失败，操作用户不存在")

    if utils.str_is_null(a_id):
        return RestResponse.failure("修改失败，a_id不能为空")

    query = AccountId.objects.filter(account_id=a_id)
    if not query.exists():
        return RestResponse.failure("修改失败，记录不存在")

    query.update(
        country=country, age=age,
        work=work, money=money, mark=mark,
        op_user_id=user.id
    )

    return RestResponse.success("更新成功")


@log_func
def account_id_del(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    a_id = body.get('a_id', "")
    logging.info("account_id_del#a_id = %s", a_id)
    if utils.str_is_null(a_id):
        return RestResponse.failure("删除失败，id不能为空")

    AccountId.objects.filter(account_id=a_id).delete()
    return RestResponse.failure("删除成功")


@log_func
def account_id_upload(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    a_id = body.get('a_id', "")
    logging.info("account_id_upload#a_id = %s", a_id)
    if utils.str_is_null(a_id):
        return RestResponse.failure("上传失败，id不能为空")

    user = request.session.get('user')
    logging.info("account_id_upload#user = %s", user.username)
    if not User.objects.filter(username=user.username).exists():
        return RestResponse.failure("上传失败，用户不存在")

    if AccountId.objects.filter(account_id=a_id).exists():
        return RestResponse.failure(f"上传失败，id={a_id}已经存在")

    AccountId.objects.create(account_id=a_id, op_user_id=user.id)
    return RestResponse.success("上传成功")


@log_func
def account_id_batch_upload(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    f = request.FILES["file"]
    if not f:
        return RestResponse.failure("上传失败，数据传输异常")

    user = request.session.get('user')
    logging.info("account_id_batch_upload#user = %s", user.username)

    if not User.objects.filter(username=user.username).exists():
        return RestResponse.failure("上传失败，用户不存在")

    name = f['name']
    logging.info("account_id_batch_upload#name = %s", name)
    ext = str(os.path.splitext(name)[-1])
    logging.info("account_id_batch_upload#ext = %s", ext)
    new_file_name = str(uuid.uuid1()) + "." + ext
    logging.info("account_id_batch_upload#new_file_name = %s", ext)
    temp_path = os.path.join(TEMP_DIR, new_file_name)
    path = handle_uploaded_file(temp_path, f)
    if not path:
        return RestResponse.failure("上传失败，保存临时文件失败")
    with open(path, 'r') as ff:
        content = ff.read().strip()
        data_list = content.split(",")
    if len(data_list) == 0:
        return RestResponse.failure("上传失败，解析内容为空")

    logging.info("account_id_batch_upload#data_list 1 = %s", data_list)

    exists_query = AccountId.objects.filter(account_id__in=data_list)

    exists_list = []
    for query in exists_query:
        i = data_list.index(query.account_id)
        if i >= 0:
            data_list.pop(i)
            exists_list.append(query.account_id)

    logging.info("account_id_batch_upload#data_list 2 = %s", data_list)
    db_data_list = []
    for data in data_list:
        db_data_list.append(AccountId.objects.create(account_id=data, op_user_id=user.id))
    AccountId.objects.bulk_create(db_data_list)
    return RestResponse.success("上传成功", data={
        'exists_ids': exists_list,
        'success_ids': data_list
    })
