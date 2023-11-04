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

from util import utils, time_utils, excel_util
from util.excel_util import ExcelBean
from util.restful import RestResponse
from util.utils import handle_uploaded_file
from web_app.dao import user_dao
from web_app.decorators.admin_decorator import log_func, api_op_user, op_admin
from web_app.model.const import UsedStatus
from web_app.model.users import User, USER_ROLE_BUSINESS, USER_ROLE_ADMIN, USER_TYPES
from web_app.service import wa_service
from web_app.settings import BASE_DIR
from web_app.util import rest_list_util

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TEMP_DIR = os.path.join(BASE_DIR, "data", 'temp')


@log_func
def wa_id_list(request: HttpRequest):
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.success_list(count=0, data=[])
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)
    back_type = body.get('back_type') or user.back_type
    queryset = wa_service.wa_id_query_set(back_type)

    if queryset:
        res, count = wa_service.search_aid_page(
            body, start_row, end_row, user, queryset
        )
    else:
        res = []
        count = 0
    return RestResponse.success_list(count=count, data=res)


@log_func
def wa_id_business_list(request: HttpRequest):
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.success_list(count=0, data=[])
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)

    # 查询记录
    start_t, end_t = time_utils.get_cur_day_time_range()
    q = Q(create_time__gte=start_t, create_time__lt=end_t) | Q(used=UsedStatus.Default)

    back_type = body.get('back_type') or user.back_type

    record_query = wa_service.wa_id_record_queryset(back_type)

    record_ids = []
    if record_query:
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

    queryset = wa_service.wa_id_query_set(back_type)

    res = []
    count = 0
    if queryset:
        queryset = rest_list_util.search_account_common_field(queryset, body)
        queryset = queryset.filter(id__in=record_ids)
        res = list(
            queryset.values(
                'id', 'account_id', 'country', 'age', 'work', 'money', 'mark', 'used',
                'op_user__username', 'create_time'
            )[start_row: end_row]
        )
        count = queryset.count()
    return RestResponse.success_list(count=count, data=res)


@log_func
def wa_dispatch_record_list(request: HttpRequest):
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

    back_type = body.get('back_type') or user.back_type
    record_query = wa_service.wa_id_record_queryset(back_type)

    record_list = []
    count = 0
    if record_query:
        logging.info("查找id分配记录是，删除用户或者accountId为空的数据")
        record_query.filter(Q(user__isnull=True) or Q(account__isnull=True)).delete()
        account_id = body.get('account_id')
        # 输入的account_id进行查询，非数据库主键
        if not utils.str_is_null(account_id):
            record_query = record_query.filter(account__account_id__contains=account_id)
        record_query = rest_list_util.search_record_common(record_query, body)
        record_list = record_query.all()[start_row: end_row]
        count = record_query.count()

    result_list = []
    for record in record_list:
        result_list.append({
            'id': record.id,
            'username': record.username,
            'account_id': record.account_id_val,
            'used': record.used,
            'create_time': record.create_time
        })

    return RestResponse.success_list(count=count, data=result_list)


@log_func
@api_op_user
def wa_id_add(request: HttpRequest):
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.failure("添加失败，未获取到登录用户信息")
    user_id = user.id
    body = utils.request_body(request)
    account_id = body.get("account_id", "")
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")

    if utils.str_is_null(account_id):
        return RestResponse.failure("添加失败，a_id不能为空")

    back_type = body.get('back_type') or user.back_type
    queryset = wa_service.wa_id_query_set(back_type)

    if not queryset:
        return RestResponse.failure("添加失败，用户状态错误")

    logging.info("添加WaId时，删除空映射的数据")
    with transaction.atomic():
        no_user_query = queryset.filter(op_user__isnull=True)
        del_ids = list(no_user_query.values_list("account_id", flat=True))
        wa_service.del_aid_with_hash(del_ids)
        no_user_query.delete()

    if wa_service.check_aid_with_hash(account_id):
        logging.info("添加Id#%s#%s#已经存在", back_type, account_id)
        return RestResponse.failure("添加失败，该id已经存在")

    wa_service.add_aid_hash(account_id, back_type, user_id)

    queryset.create(
        account_id=account_id, country=country, age=age,
        work=work, money=money, mark=mark,
        op_user_id=user_id,
        create_time=time_utils.get_now_bj_time_str(),
        update_time=time_utils.get_now_bj_time_str()
    )

    return RestResponse.success("添加成功")


@log_func
@api_op_user
def wa_id_update(request: HttpRequest):
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.failure("添加失败，未获取到登录用户信息")
    user_id = user.id

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

    back_type = body.get('back_type') or user.back_type
    queryset = wa_service.wa_id_query_set(back_type)
    record_query = wa_service.wa_id_record_queryset(back_type)

    if not queryset or not record_query:
        return RestResponse.failure("添加失败，用户状态错误")

    queryset = queryset.filter(id=int(a_id), op_user__isnull=False)
    if not queryset.exists():
        return RestResponse.failure("修改失败，记录不存在")

    role = request.session.get('user').get('role')
    is_business_user = role == USER_ROLE_BUSINESS
    is_admin = role == USER_ROLE_ADMIN
    upd_field = {
        "account_id": account_id, "country": country, "age": age,
        "work": work, "money": money, "mark": mark,
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

                _q = record_query.filter(account_id=a_id)
                if _q.exists():
                    logging.info("管理员编辑为%s，同步更新记录状态", _status)
                    _q.update(used=_status, update_time=time_utils.get_now_bj_time_str())
            elif is_business_user:
                logging.info("业务员编辑, 直接状态为 = %s", str(_status))
                upd_field['used'] = _status
                _q = record_query.filter(user_id=user_id, account_id=a_id)
                if _q.exists():
                    logging.info("业务员编辑为%s，同步更新记录状态", _status)
                    _q.update(used=_status, update_time=time_utils.get_now_bj_time_str())

        logging.info("要跟新的字段 = %s", upd_field)
        queryset.update(**upd_field)

    return RestResponse.success("更新成功")


@log_func
@api_op_user
@op_admin
def wa_id_del(request: HttpRequest):
    body = utils.request_body(request)
    logging.info("删除ID账号#body = %s", body)
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.failure("添加失败，未获取到登录用户信息")

    back_type = body.get('back_type') or user.back_type
    queryset = wa_service.wa_id_query_set(back_type)
    record_query = wa_service.wa_id_record_queryset(back_type)

    if not queryset or not record_query:
        return RestResponse.failure("添加失败，用户状态错误")

    account_id = body.get('account_id', "")
    logging.info("wa_account_id2_del#a_id = %s", account_id)
    if utils.str_is_null(account_id):
        return RestResponse.failure("删除失败，id不能为空")

    with transaction.atomic():
        wa_service.del_aid_with_hash([account_id])
        record_query.filter(account__account_id=account_id).delete()
        queryset.filter(account_id=account_id).delete()

    return RestResponse.success("删除成功")


@log_func
@api_op_user
def wa_id_upload(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    a_id = str(body.get('account_id', "")).strip()
    logging.info("account_wa2_id_upload#a_id = %s", a_id)
    if utils.str_is_null(a_id):
        return RestResponse.failure("上传失败，id不能为空")

    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.failure("添加失败，未获取到登录用户信息")

    if wa_service.check_id(a_id):
        return RestResponse.failure("添加失败，该Id已经存在")

    user_id = user.id
    back_type = body.get('back_type') or user.back_type
    queryset = wa_service.wa_id_query_set(back_type)

    if not queryset:
        return RestResponse.failure("添加失败，用户状态错误")

    logging.info("添加WaId时，删除空映射的数据")
    with transaction.atomic():
        no_user_query = queryset.filter(op_user__isnull=True)
        del_ids = list(no_user_query.values_list("account_id", flat=True))
        wa_service.del_aid_with_hash(del_ids)
        no_user_query.delete()

        wa_service.add_aid_hash(a_id, back_type, user_id)
        query, created = queryset.get_or_create(
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
def wa_id_batch_upload(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    f = request.FILES["file"]
    filename = request.POST["filename"]
    if not f:
        return RestResponse.failure("上传失败，数据传输异常")

    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
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

    user_id = user.id
    back_type = request.POST['back_type'] or user.back_type
    queryset = wa_service.wa_id_query_set(back_type)

    record_query = wa_service.wa_id_record_queryset(back_type)

    if not queryset or not record_query:
        return RestResponse.failure("添加失败，用户状态错误")

    if wa_service.check_id_list(data_list):
        return RestResponse.failure("上传失败，ID均已存在，无法上传")

    # exists_query = queryset.filter(account_id__in=data_list)
    #
    # exists_list = []
    # for query in exists_query:
    #     i = data_list.index(query.account_id)
    #     if i >= 0:
    #         data_list.pop(i)
    #         exists_list.append(query.account_id)
    # if len(data_list) == 0:
    #     return RestResponse.failure("上传失败，ID均已存在，无法上传")
    logging.info("account_id_batch_upload#data_list 2 = %s", len(data_list))
    db_data_list = []
    ids = []
    for data in data_list:
        create_dict = {
            "account_id": data, 'op_user_id': int(user_id),
            'create_time': time_utils.get_now_bj_time_str(),
            'update_time': time_utils.get_now_bj_time_str()
        }
        model = wa_service.wa_id_create_model(back_type, **create_dict)

        if model:
            db_data_list.append(model)
            ids.append(data)
    with transaction.atomic():
        no_user_query = queryset.filter(op_user__isnull=True)
        del_ids = list(no_user_query.values_list("account_id", flat=True))
        wa_service.del_aid_with_hash(del_ids)
        no_user_query.delete()
        for _id in ids:
            wa_service.add_aid_hash(_id, back_type, user_id)
        queryset.bulk_create(db_data_list)
    return RestResponse.success("上传成功", data={
        'success_ids': data_list
    })


@csrf_exempt
@log_func
@api_op_user
def wa_id_export(request):
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.failure("导出，未获取到登录用户信息")

    user_id = user.id
    body = utils.request_body(request)

    back_type = body.get('back_type') or user.back_type
    queryset = wa_service.wa_id_query_set(back_type)

    if not queryset:
        return RestResponse.failure("失败，用户状态错误")

    if request.session['user'].get('role') == USER_ROLE_ADMIN:
        logging.info("管理员导出全部数据")
        # 管理员导出全部数据
        query_list = list(queryset.all())
    else:
        logging.info("非管理员导出自身当天全部数据")
        start, end = time_utils.get_cur_day_time_range()
        # 非管理员导出当天数据
        query_list = list(
            queryset.filter(op_user_id=user_id, create_time__gte=start, create_time__lt=end).all()
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
def wa_handle_dispatcher(request: HttpRequest):
    body = utils.request_body(request)
    is_all = utils.is_bool_val(body.get("isAll"))
    back_type = body.get('back_type')
    if not back_type or int(back_type) not in USER_TYPES:
        return RestResponse.failure("分发错误，backType类型错误")

    try:
        queryset = wa_service.wa_id_query_set(back_type)

        record_query = wa_service.wa_id_record_queryset(back_type)
        record_type = wa_service.get_record_type(back_type)

        code, msg = wa_service.dispatcher_aid(queryset, back_type, record_query, record_type, is_all)
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
    back_type = body.get('back_type')
    if not back_type or int(back_type) not in USER_TYPES:
        return RestResponse.failure("错误，backType类型错误")
    queryset = wa_service.wa_id_query_set(back_type)
    record_query = wa_service.wa_id_record_queryset(back_type)
    try:
        ids = body.get("ids", "")
        ids = ids.split(",")
        used = body.get('used')
        used = utils.get_status(used)
        queryset.filter(id__in=ids).update(used=used)
        record_query.filter(account__id__in=ids).update(used=used)
        return RestResponse.success()
    except BaseException as e:
        logging.info("批量修改使用状态失败 %s => %s", str(e), traceback.format_exc())
        return RestResponse.failure("批量修改失败")


@log_func
def sync_id_hash(request):
    wa_service.sync_id_hash()
    return RestResponse.success("成功")


@log_func
def sync_qr_hash(request):
    wa_service.sync_qr_hash()
    return RestResponse.success("成功")


@log_func
def sync_used(request: HttpRequest):
    wa_service.sync_used_id()
    wa_service.sync_used_qr()
    return RestResponse.success("成功")
