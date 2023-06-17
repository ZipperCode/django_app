import logging
import os
import uuid
from typing import List

from django.http import HttpRequest, HttpResponse, FileResponse
from django.utils.encoding import escape_uri_path
from django.views.decorators.csrf import csrf_exempt

from util import utils, time_utils, excel_util, http_utils
from util.excel_util import ExcelBean
from util.restful import RestResponse
from util.utils import handle_uploaded_file
from web_app.dao import account_dao, user_dao
from web_app.decorators.admin_decorator import log_func, api_op_user, op_admin
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
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.success_list(count=0, data=[])
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)
    res, count = account_dao.search_account_id_page(body, start_row, end_row, user)
    return RestResponse.success_list(count=count, data=res)


@log_func
@api_op_user
def account_id_add(request: HttpRequest):
    user_id = request.session.get('user_id')
    if not http_utils.check_user_id(user_id):
        return RestResponse.failure("添加失败，未获取到登录用户信息")

    body = utils.request_body(request)
    account_id = body.get("account_id", "")
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")

    if utils.str_is_null(account_id):
        return RestResponse.failure("添加失败，a_id不能为空")

    if AccountId.objects.filter(account_id=account_id).exists():
        return RestResponse.failure("添加失败，该id已经存在")

    AccountId.objects.create(
        account_id=account_id, country=country, age=age,
        work=work, money=money, mark=mark,
        op_user_id=user_id,
        create_time=time_utils.get_now_bj_time(),
        update_time=time_utils.get_now_bj_time()
    )

    return RestResponse.success("添加成功")


@log_func
@api_op_user
def account_id_update(request: HttpRequest):
    user_id = request.session.get('user_id')
    if not http_utils.check_user_id(user_id):
        return RestResponse.failure("修改失败，未获取到登录用户信息")

    body = utils.request_body(request)
    account_id = body.get("account_id", "")
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")

    if utils.str_is_null(account_id):
        return RestResponse.failure("修改失败，a_id不能为空")

    query = AccountId.objects.filter(account_id=account_id)
    if not query.exists():
        return RestResponse.failure("修改失败，记录不存在")

    query.update(
        country=country, age=age,
        work=work, money=money, mark=mark,
        op_user_id=int(user_id),
        update_time=time_utils.get_now_bj_time()
    )

    return RestResponse.success("更新成功")


@log_func
@api_op_user
@op_admin
def account_id_del(request: HttpRequest):
    body = utils.request_body(request)
    logging.info("删除ID账号#body = %s", body)
    user_id = request.session.get('user_id')
    if not http_utils.check_user_id(user_id):
        return RestResponse.failure("删除失败，未获取到登录用户信息")
    a_id = body.get('id', "")
    account_id = body.get('account_id', "")
    logging.info("account_id_del#a_id = %s", account_id)
    if utils.str_is_null(account_id):
        return RestResponse.failure("删除失败，id不能为空")

    AccountId.objects.filter(account_id=account_id).delete()
    return RestResponse.success("删除成功")


@log_func
@api_op_user
def account_id_upload(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    a_id = body.get('account_id', "")
    logging.info("account_id_upload#a_id = %s", a_id)
    if utils.str_is_null(a_id):
        return RestResponse.failure("上传失败，id不能为空")

    user_id = request.session.get('user_id')
    if not http_utils.check_user_id(user_id):
        return RestResponse.failure("上传，未获取到登录用户信息")

    query = AccountId.objects.filter(account_id=a_id)
    if query.exists():
        return RestResponse.failure(f"上传失败，id={a_id}已经存在")

    AccountId.objects.create(
        account_id=a_id, op_user_id=int(user_id),
        create_time=time_utils.get_now_bj_time(),
        update_time=time_utils.get_now_bj_time()
    )
    return RestResponse.success("上传成功")


@log_func
@api_op_user
def account_id_batch_upload(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    f = request.FILES["file"]
    filename = request.POST["filename"]
    if not f:
        return RestResponse.failure("上传失败，数据传输异常")

    user_id = request.session.get('user_id')
    if not http_utils.check_user_id(user_id):
        return RestResponse.failure("上传，未获取到登录用户信息")

    logging.info("batch_upload = %s", f)
    logging.info("account_id_batch_upload#name = %s", filename)
    ext = str(os.path.splitext(filename)[-1])
    logging.info("account_id_batch_upload#ext = %s", ext)
    new_file_name = str(uuid.uuid1()) + ext
    logging.info("account_id_batch_upload#new_file_name = %s", ext)
    temp_path = os.path.join(TEMP_DIR, new_file_name)
    path = handle_uploaded_file(temp_path, f)
    if not path:
        return RestResponse.failure("上传失败，保存临时文件失败")

    data_list = []
    with open(path, 'r') as ff:
        lines = ff.readlines()
        for line in lines:
            data_list += line.strip().split(",")
    os.remove(path)
    if len(data_list) == 0:
        return RestResponse.failure("上传失败，解析内容为空")
    data_list = list(set(data_list))
    logging.info("account_id_batch_upload#data_list 1 = %s", data_list)

    exists_query = AccountId.objects.filter(account_id__in=data_list)

    exists_list = []
    for query in exists_query:
        i = data_list.index(query.account_id)
        if i >= 0:
            data_list.pop(i)
            exists_list.append(query.account_id)
    if len(data_list) == 0:
        return RestResponse.failure("上传失败，ID均已存在，无法上传")
    logging.info("account_id_batch_upload#data_list 2 = %s", len(data_list))
    db_data_list = []
    for data in data_list:
        db_data_list.append(AccountId(
            account_id=data, op_user_id=int(user_id),
            create_time=time_utils.get_now_bj_time(),
            update_time=time_utils.get_now_bj_time()
        ))
    AccountId.objects.bulk_create(db_data_list)
    return RestResponse.success("上传成功", data={
        'exists_ids': exists_list,
        'success_ids': data_list
    })


@csrf_exempt
@log_func
@api_op_user
def account_id_export(request):
    user_id = request.session.get('user_id')
    if not http_utils.check_user_id(user_id):
        return RestResponse.failure("导出，未获取到登录用户信息")

    query_list = list(AccountId.objects.all())
    logging.info("export id # 数据大小 = %s", len(query_list))
    excel_list: List[ExcelBean] = list()
    for data in query_list:
        excel_list.append(ExcelBean(
            id=data.account_id,
            country=data.country,
            age=data.age,
            work=data.work,
            mark=data.mark,
            money=data.money,
            op_user=data.op_user_name,
            upload_time=time_utils.fmt_datetime(data.create_time),
        ))
    logging.info("export_id# 转换ExcelBean成功 = %s", len(excel_list))
    temp_path = os.path.join(TEMP_DIR, "excel")
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)
    logging.info("export_id#开始生成excel文件，目录 = %s", temp_path)
    file_path = excel_util.create_excel(excel_list, temp_path)
    logging.info("export_id#生成临时Excel文件成功，文件 = %s", file_path)
    if not file_path:
        return HttpResponse(status=404, content="下载失败，创建excel失败")

    file = open(file_path, 'rb')
    file_name = os.path.basename(file_path)
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="' + escape_uri_path(file_name) + '"'
    return response
