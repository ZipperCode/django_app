import logging
import os
import traceback
import uuid
from typing import List

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, FileResponse
from django.utils.encoding import escape_uri_path
from django.views.decorators.csrf import csrf_exempt

from util import utils, time_utils, excel_util, http_utils
from util.excel_util import ExcelBean
from util.restful import RestResponse
from util.utils import handle_uploaded_file
from web_app.dao import user_dao, wa2_dao
from web_app.decorators.admin_decorator import log_func, api_op_user, op_admin
from web_app.model.const import UsedStatus
from web_app.model.users import User, USER_ROLE_BUSINESS, USER_ROLE_ADMIN, UserAccountRecord
from web_app.model.wa_accounts2 import WaUserIdRecord2, WaAccountId2
from web_app.settings import BASE_DIR
from web_app.util import rest_list_util

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TEMP_DIR = os.path.join(BASE_DIR, "data", 'temp')


@log_func
def wa2_account_id_list(request: HttpRequest):
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.success_list(count=0, data=[])
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)
    res, count = wa2_dao.search_account_id_page(body, start_row, end_row, user)
    return RestResponse.success_list(count=count, data=res)


@log_func
def wa2_account_id_business_list(request: HttpRequest):
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.success_list(count=0, data=[])
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)

    # 查询记录
    start_t, end_t = time_utils.get_cur_day_time_range()
    q = Q(create_time__gte=start_t, create_time__lt=end_t) | Q(used=UsedStatus.Default)
    record_query = WaUserIdRecord2.objects
    account_id = body.get("account_id", "")
    if not utils.str_is_null(account_id):
        logging.info("添加账号id过滤")
        record_query = record_query.filter(account__account_id__contains=account_id)

    record_ids = list(
        map(
            lambda x: x.get('account_id'),
            list(
                record_query.filter(user_id=user.id).filter(q).distinct()
                .order_by('user_id', 'account_id').values('account_id')
            )
        )
    )

    if len(record_ids) == 0:
        logging.info("当前用户没有可分配的数据，返回空数据")
        return RestResponse.success_list(count=0, data=[])

    logging.info("当前用户所分配的ids = %s", record_ids)

    query = rest_list_util.search_account_common_field(WaAccountId2.objects, body)
    query = query.filter(id__in=record_ids)
    res = list(
        query.values(
            'id', 'account_id', 'country', 'age', 'work', 'money', 'mark', 'used',
            'op_user__username', 'create_time'
        )[start_row: end_row]
    )
    res, count = list(res), query.count()
    return RestResponse.success_list(count=count, data=res)


@log_func
def wa2_dispatch_record_list(request: HttpRequest):
    """
    分配给用户的数据
    """
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.success_list(count=0, data=[])
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)
    logging.info("ID分配记录搜索 用户 = %s, body = %s", user.username, body)
    # 记录列表
    query = WaUserIdRecord2.objects.filter(user__isnull=False, account__isnull=False)
    account_id = body.get('account_id')
    # 输入的account_id进行查询，非数据库主键
    if not utils.str_is_null(account_id):
        query = query.filter(account__account_id__contains=account_id)
    query = rest_list_util.search_record_common(query, body)
    record_list = query.all()[start_row: end_row]
    result_list = []
    for record in record_list:
        result_list.append({
            'id': record.id,
            'username': record.username,
            'account_id': record.account_id_val,
            'used': record.used,
            'create_time': record.create_time
        })

    return RestResponse.success_list(count=query.count(), data=result_list)


@log_func
@api_op_user
def wa2_account_id_add(request: HttpRequest):
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

    if WaAccountId2.objects.filter(account_id=account_id, op_user__isnull=False).exists():
        return RestResponse.failure("添加失败，该id已经存在")

    WaAccountId2.objects.create(
        account_id=account_id, country=country, age=age,
        work=work, money=money, mark=mark,
        op_user_id=user_id,
        create_time=time_utils.get_now_bj_time_str(),
        update_time=time_utils.get_now_bj_time_str()
    )

    return RestResponse.success("添加成功")


@log_func
@api_op_user
def wa2_account_id_update(request: HttpRequest):
    user_id = request.session.get('user_id')
    if not http_utils.check_user_id(user_id):
        return RestResponse.failure("修改失败，未获取到登录用户信息")

    body = utils.request_body(request)
    a_id = body.get('id')
    account_id = body.get("account_id", "")
    if utils.str_is_null(a_id) or not utils.is_int(a_id):
        return RestResponse.failure("修改失败，主键为空或异常")

    if utils.str_is_null(account_id):
        return RestResponse.failure("修改失败，a_id不能为空")

    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")
    used = body.get('used')

    query = WaAccountId2.objects.filter(id=int(a_id), op_user__isnull=False)
    if not query.exists():
        return RestResponse.failure("修改失败，记录不存在")

    role = request.session.get('user').get('role')
    is_business_user = role == USER_ROLE_BUSINESS
    is_admin = role == USER_ROLE_ADMIN
    upd_field = {
        "account_id": account_id, "country": country, "age": age,
        "work": work, "money": money, "mark": mark,
        "op_user_id": int(user_id),
        "update_time": time_utils.get_now_bj_time_str()
    }

    with transaction.atomic():
        if not utils.str_is_null(used):
            _status = utils.get_status(used)
            logging.info("修改状态，当前状态值为%s", str(_status))
            if is_admin:
                upd_field['used'] = _status
                logging.info("管理员编辑，且数据的状态为 %s, 修改", used)
                if _status == UsedStatus.Used:
                    # 修改is_bind=True，分发的时候就过滤这个了
                    upd_field['is_bind'] = True
                    logging.info("管理员编辑为已使用，同步更新记录状态")
                _q = WaUserIdRecord2.objects.filter(account_id=account_id)
                if _q.exists():
                    _q.update(used=_status, update_time=time_utils.get_now_bj_time_str())
            elif is_business_user:
                logging.info("业务员编辑, 直接状态为 = %s", str(_status))
                upd_field['used'] = _status
                del upd_field['op_user_id']
                _q = WaUserIdRecord2.objects.filter(user_id=user_id, account_id=account_id)
                if _q.exists():
                    _q.update(used=_status, update_time=time_utils.get_now_bj_time_str())

        logging.info("要跟新的字段 = %s", upd_field)
        query.update(**upd_field)

    return RestResponse.success("更新成功")


@log_func
@api_op_user
@op_admin
def wa2_account_id_del(request: HttpRequest):
    body = utils.request_body(request)
    logging.info("删除ID账号#body = %s", body)
    user_id = request.session.get('user_id')
    if not http_utils.check_user_id(user_id):
        return RestResponse.failure("删除失败，未获取到登录用户信息")
    a_id = body.get('id', "")
    account_id = body.get('account_id', "")
    logging.info("wa_account_id2_del#a_id = %s", account_id)
    if utils.str_is_null(account_id):
        return RestResponse.failure("删除失败，id不能为空")
    WaUserIdRecord2.objects.filter(account__account_id=account_id).delete()
    WaAccountId2.objects.filter(account_id=account_id).delete()
    return RestResponse.success("删除成功")


@log_func
@api_op_user
def wa2_account_id_upload(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    a_id = str(body.get('account_id', "")).strip()
    logging.info("account_wa2_id_upload#a_id = %s", a_id)
    if utils.str_is_null(a_id):
        return RestResponse.failure("上传失败，id不能为空")

    user_id = request.session.get('user_id')
    if not http_utils.check_user_id(user_id):
        logging.info("account_wa2_id_upload#上传失败，未获取到用户信息")
        return RestResponse.failure("上传，未获取到登录用户信息")

    query, created = WaAccountId2.objects.get_or_create(
        account_id=a_id,
        defaults={
            'op_user_id': int(user_id),
            "create_time": time_utils.get_now_bj_time_str(),
            "update_time": time_utils.get_now_bj_time_str()
        }
    )
    if not created:
        logging.info("account_wa2_id_upload#已经存在")
        return RestResponse.failure(f"上传失败，id={a_id}已经存在")

    return RestResponse.success("上传成功")


@log_func
@api_op_user
def wa2_account_id_batch_upload(request: HttpRequest):
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
    data_list = list(map(lambda x: str(x).strip(), data_list))

    exists_query = WaAccountId2.objects.filter(account_id__in=data_list)

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
        db_data_list.append(WaAccountId2(
            account_id=data, op_user_id=int(user_id),
            create_time=time_utils.get_now_bj_time_str(),
            update_time=time_utils.get_now_bj_time_str()
        ))

    WaAccountId2.objects.bulk_create(db_data_list)
    return RestResponse.success("上传成功", data={
        'exists_ids': exists_list,
        'success_ids': data_list
    })


@csrf_exempt
@log_func
@api_op_user
def wa2_account_id_export(request):
    user_id = request.session.get('user_id')
    if not http_utils.check_user_id(user_id):
        return RestResponse.failure("导出，未获取到登录用户信息")

    if request.session['user'].get('role') == USER_ROLE_ADMIN:
        logging.info("管理员导出全部数据")
        # 管理员导出全部数据
        query_list = list(WaAccountId2.objects.all())
    else:
        logging.info("非管理员导出自身当天全部数据")
        start, end = time_utils.get_cur_day_time_range()
        # 非管理员导出当天数据
        query_list = list(
            WaAccountId2.objects.filter(op_user_id=user_id, create_time__gte=start, create_time__lt=end).all()
        )
    logging.info("wa_account_id2_export# 数据大小 = %s", len(query_list))
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
    logging.info("wa_account_id2_export# 转换ExcelBean成功 = %s", len(excel_list))
    temp_path = os.path.join(TEMP_DIR, "excel")
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
    logging.info("wa_account_id2_export#开始生成excel文件，目录 = %s", temp_path)
    file_path = excel_util.create_excel(excel_list, temp_path)
    logging.info("wa_account_id2_export#生成临时Excel文件成功，文件 = %s", file_path)
    if not file_path:
        return HttpResponse(status=404, content="下载失败，创建excel失败")

    file = open(file_path, 'rb')
    file_name = os.path.basename(file_path)
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="' + escape_uri_path(file_name) + '"'
    return response


@log_func
def wa2_handle_dispatcher(request: HttpRequest):
    body = utils.request_body(request)
    is_all = utils.is_bool_val(body.get("isAll"))
    try:
        code, msg = wa2_dao.dispatcher_account_id(is_all)
        if code < 0:
            return RestResponse.failure(str(msg))
        return RestResponse.success(msg)
    except BaseException as e:
        logging.info("handle_dispatcher# e = %s trace = %s", str(e), traceback.format_exc())
        return RestResponse.failure("分发错误，请联系管理员")


@log_func
def handle_used_state(request: HttpRequest):
    body = utils.request_body(request)
    logging.info("批量修改使用状态#wa2_id#body = %s", str(body))
    try:
        ids = body.get("ids", "")
        ids = ids.split(",")
        used = body.get('used')
        used = utils.get_status(used)
        WaAccountId2.objects.filter(id__in=ids).update(used=used)
        WaUserIdRecord2.objects.filter(account__id__in=ids).update(used=used)
        return RestResponse.success()
    except BaseException as e:
        logging.info("批量修改使用状态失败 %s => %s", str(e), traceback.format_exc())
        return RestResponse.failure("批量修改失败")
