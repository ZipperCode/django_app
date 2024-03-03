import logging
import os
import shutil
import traceback
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from typing import List

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, FileResponse
from django.utils.encoding import escape_uri_path

from util import utils, qr_util, time_utils, excel_util
from util.excel_util import ExcelBean
from util.restful import RestResponse
from util.utils import handle_uploaded_file
from web_app.dao import user_dao
from web_app.decorators.admin_decorator import log_func, api_op_user, op_admin
from web_app.decorators.restful_decorator import api_post
from web_app.model.const import UsedStatus
from web_app.model.users import User, USER_ROLE_ADMIN, USER_ROLE_BUSINESS, USER_TYPES
from web_app.model.wa_accounts import WaAccountQr
from web_app.service import wa_service
from web_app.settings import BASE_DIR, MEDIA_ROOT
from web_app.util import rest_list_util, wa_util

from util.exception import BusinessException

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TEMP_DIR = os.path.join(BASE_DIR, "data", 'temp')


@log_func
@api_op_user
def wa_qr_list(request: HttpRequest):
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.failure("获取信息失败，用户未登录")

    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)

    back_type = body.get('back_type') or user.back_type
    queryset = wa_service.wa_qr_queryset(back_type)
    if not queryset:
        return RestResponse.success_list(count=0, data=[])
    res, count = wa_service.search_aqr_page(body, start_row, end_row, user, queryset)
    return RestResponse.success_list(count=count, data=res)


@log_func
def wa_qr_business_list(request: HttpRequest):
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)

    # 查询记录
    start_t, end_t = time_utils.get_cur_over_7day_time_range()
    logging.info("当前时间 = %s", start_t)
    logging.info("七天前时间 = %s", end_t)
    q = Q(used=UsedStatus.Default) | Q(used=UsedStatus.Used)
    back_type = body.get('back_type')
    queryset = wa_service.wa_qr_queryset(back_type)
    record_queryset = wa_service.wa_qr_record_queryset(back_type)
    if not queryset or not record_queryset:
        logging.info("backType错误，%s", back_type)
        return RestResponse.success_list(count=0, data=[])
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.failure("user is none")
    record_ids = list(
        map(
            lambda x: x.get('account_id'),
            list(
                record_queryset.filter(user_id=user.id).filter(
                    Q(create_time__gte=start_t, create_time__lt=end_t)
                ).filter(q).distinct()
                .order_by('user_id', 'account_id').values('account_id')
            )
        )
    )

    if len(record_ids) == 0:
        logging.info("当前用户没有可分配的数据，返回空数据")
        return RestResponse.success_list(count=0, data=[])

    logging.info("当前用户所分配的ids = %s", record_ids)

    query = rest_list_util.search_account_common_field(queryset, body)
    query = query.filter(id__in=record_ids)
    res = list(
        query.values(
            'id', 'qr_content', 'qr_path', 'country', 'age', 'work', 'money', 'mark', 'link_mark', 'used',
            'op_user__username', 'create_time', 'update_time'
        )[start_row: end_row]
    )
    res, count = list(res), query.count()
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
    logging.info("二维码分配记录搜索 用户 = %s, body = %s", user.username, body)
    # 记录列表
    back_type = body.get('back_type') or user.back_type
    record_queryset = wa_service.wa_qr_record_queryset(back_type)
    if not record_queryset:
        logging.info("backType错误，%s", back_type)
        return RestResponse.success_list(count=0, data=[])

    query = record_queryset.filter(user__isnull=False, account__isnull=False)
    query = rest_list_util.search_record_common(query, body)
    record_list = list(query.all()[start_row: end_row])

    result_list = []
    for record in record_list:
        result_list.append({
            'id': record.id,
            'username': record.username,
            'account_qr': record.account_qr,
            'used': record.used,
            'create_time': record.create_time
        })

    return RestResponse.success_list(count=query.count(), data=result_list)


@log_func
def wa_qr_add(request: HttpRequest):
    body = utils.request_body(request)
    qr = request.FILES['qr_file']
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")
    link_mark = body.get('link_mark', "")

    user = request.session.get('user')
    logging.info("account_id_upload#user = %s", user.username)
    user = user_dao.get_user(request)
    if not user:
        return RestResponse.failure("添加失败，操作用户不存在")

    qr_content = "content"
    if utils.str_is_null(qr_content):
        return RestResponse.failure("添加失败，解析二维码失败")

    back_type = body.get('back_type') or user.back_type
    queryset = wa_service.wa_qr_queryset(back_type)
    if not queryset:
        logging.info("backType错误，%s", back_type)
        return RestResponse.failure(f"添加失败backType错误 {back_type}")

    if wa_service.check_aqr_with_hash(qr_content):
        logging.info("添加Qr#%s#%s#已经存在", back_type, qr_content)
        return RestResponse.failure("添加失败，该Qr已经存在")

    logging.info("添加WaQr时，删除空映射的数据")
    with transaction.atomic():
        no_user_query = queryset.filter(op_user__isnull=True)
        del_qr_contents = list(no_user_query.values_list("qr_content", flat=True))
        wa_service.del_aqr_with_hash(del_qr_contents)
        no_user_query.delete()
        wa_service.add_aqr_hash(qr_content, back_type, user.id)

        queryset.create(
            qr_content=qr_content, qr_path=qr, country=country, age=age,
            work=work, money=money, mark=mark, link_mark=link_mark,
            op_user_id=user.id
        )

    return RestResponse.success("添加成功")


@api_post
@api_op_user
def wa_qr_update(request: HttpRequest):
    body = utils.request_body(request)
    logging.info("qr_update# body = %s", str(body))
    db_id = body.get('id', "")
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")
    link_mark = body.get('link_mark', "")
    used = body.get('used')
    if utils.str_is_null(db_id) or not utils.is_int(db_id):
        return RestResponse.failure("修改失败，id不能为空或只能数字")

    user = user_dao.get_user(request)
    if not user:
        return RestResponse.failure("添加失败，操作用户不存在")

    user_id = user.id
    back_type = body.get('back_type') or user.back_type
    queryset = wa_service.wa_qr_queryset(back_type)
    record_queryset = wa_service.wa_qr_record_queryset(back_type)
    if not queryset or not record_queryset:
        return RestResponse.failure(f"失败，用户类型错误 {back_type}")

    queryset = queryset.filter(id=db_id)
    if not queryset.exists():
        return RestResponse.failure("修改失败，记录不存在")
    role = request.session.get('user').get('role')
    is_business_user = role == USER_ROLE_BUSINESS
    is_admin = role == USER_ROLE_ADMIN
    upd_field = {
        "country": country, "age": age,
        "work": work, "money": money, "mark": mark, "link_mark": link_mark,
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
                _q = record_queryset.filter(account_id=db_id)
                if _q.exists():
                    _q.update(used=_status, update_time=time_utils.get_now_bj_time_str())
                elif _status == UsedStatus.Used:
                    return RestResponse.failure("失败，该条数据还未分配, 无法修改为已使用")
                # else:
                #     create_dict = {
                #         'user_id': user_id,
                #         'account_id': db_id,
                #         'used': UsedStatus.Default,
                #         'create_time': time_utils.get_now_bj_time_str(),
                #         'update_time': time_utils.get_now_bj_time_str()
                #     }
                #     wa_service.wa_qr_record_create_model(back_type, **create_dict)
            elif is_business_user:
                logging.info("业务员编辑, 直接状态为 = %s", str(_status))
                upd_field['used'] = _status
                _q = record_queryset.filter(user_id=user_id, account_id=db_id)
                if _q.exists():
                    _q.update(used=_status, update_time=time_utils.get_now_bj_time_str())
                else:
                    return RestResponse.failure("修改失败，记录不存在")
                    # create_dict = {
                    #     'user_id': user_id,
                    #     'account_id': db_id,
                    #     'used': UsedStatus.Default,
                    #     'create_time': time_utils.get_now_bj_time_str(),
                    #     'update_time': time_utils.get_now_bj_time_str()
                    # }
                    # wa_service.wa_qr_record_create_model(back_type, **create_dict)
        queryset.update(**upd_field)

    return RestResponse.success("更新成功")


@log_func
@op_admin
def wa_qr_del(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    id_ = body.get('id', "")
    logging.info("WaQrDel#id_ = %s", id_)
    if utils.str_is_null(id_) or not utils.is_int(id_):
        return RestResponse.failure("删除失败，id不能为空或只能数字")

    user = user_dao.get_user(request)
    if not user:
        return RestResponse.failure("添加失败，操作用户不存在")

    back_type = body.get('back_type') or user.back_type
    queryset = wa_service.wa_qr_queryset(back_type)
    record_queryset = wa_service.wa_qr_record_queryset(back_type)
    if not queryset or not record_queryset:
        return RestResponse.failure(f"失败，用户类型错误 {back_type}")

    queryset = queryset.filter(id=id_)
    if queryset.exists():
        try:
            qr_path = os.path.join(MEDIA_ROOT, str(queryset.first().qr_path))
            if os.path.exists(qr_path) and os.path.isfile(qr_path):
                os.remove(qr_path)
        except BaseException:
            logging.info("WaQrDel#删除记录同时删除上传图片失败，trace %s", traceback.format_exc())
        finally:
            with transaction.atomic():
                if queryset.exists():
                    qr_content = queryset.first().qr_content
                    wa_service.del_aqr_with_hash([qr_content])
                record_queryset.filter(account_id=id_).delete()
                queryset.delete()
    return RestResponse.success("删除成功")


@log_func
@api_op_user
def wa_qr_upload(request: HttpRequest):
    f = request.FILES["image"]
    filename = request.POST["filename"]
    if not f:
        return HttpResponse("上传失败，数据传输异常")
    if request.session.get('in_used'):
        return RestResponse.failure("上传失败，正在处理中")
    request.session['in_used'] = True
    temp_path = None

    user = user_dao.get_user(request)
    if not user:
        return RestResponse.failure("失败，操作用户不存在")

    back_type = request.POST['back_type'] or user.back_type
    queryset = wa_service.wa_qr_queryset(back_type)
    if not queryset:
        return RestResponse.failure(f"失败，用户类型错误 {back_type}")

    try:
        user_id = request.session.get('user_id')
        if not user_id or utils.str_is_null(user_id):
            return RestResponse.failure("上传失败，未获取到登录用户信息")

        logging.info("account_qr_upload# f = %s", type(f))
        logging.info("account_qr_upload#name = %s", filename)
        ext = str(os.path.splitext(filename)[-1])
        logging.info("account_qr_upload#ext = %s", ext)
        new_file_name = str(uuid.uuid1()) + ext
        logging.info("account_id_batch_upload#new_file_name = %s", ext)
        temp_path = os.path.join(TEMP_DIR, new_file_name)
        path = handle_uploaded_file(temp_path, f)
        logging.info("上传图片，临时文件为 = %s", temp_path)
        if not path or not os.path.exists(temp_path):
            return RestResponse.failure("上传失败，保存临时文件失败")

        # 识别图片
        parsed = qr_util.get_qr_code(temp_path)
        # os.remove(temp_path)
        logging.info("account_qr_upload#parsed = %s", parsed)
        if not parsed:
            return RestResponse.failure("上传失败，无法解析二维码")

        if wa_service.check_qr(str(parsed).strip()):
            return RestResponse.failure("上传失败，二维码已经存在")
        f.name = str(uuid.uuid1()) + ext

        with transaction.atomic():
            no_user_query = queryset.filter(op_user__isnull=True)
            del_ids = list(no_user_query.values_list("qr_content", flat=True))
            wa_service.del_aqr_with_hash(del_ids)
            no_user_query.delete()

            wa_service.add_aqr_hash(parsed, back_type, user_id)
            queryset.create(
                qr_content=str(parsed).strip(),
                qr_path=f,
                op_user_id=user_id
            )
        return RestResponse.success("上传成功")
    finally:
        if temp_path is not None and os.path.exists(temp_path) and os.path.isfile(temp_path):
            os.remove(temp_path)
        request.session['in_used'] = False


@log_func
@api_op_user
def wa_qr_batch_upload(request: HttpRequest):
    f = request.FILES["file"]
    if not f:
        return HttpResponse("上传失败，数据传输异常")

    user = user_dao.get_user(request)
    if not user:
        return RestResponse.failure("失败，操作用户不存在")
    user_id = user.id
    back_type = request.POST['back_type'] or user.back_type
    queryset = wa_service.wa_qr_queryset(back_type)
    if not queryset:
        return RestResponse.failure(f"失败，用户类型错误 {back_type}")

    ext = str(os.path.splitext(f.name)[-1])
    logging.info("account_qr_batch_upload#ext = %s", ext)
    f_name = str(uuid.uuid1())
    new_file_name = f_name + ext
    logging.info("account_qr_batch_upload#new_file_name = %s", new_file_name)
    temp_path = os.path.join(TEMP_DIR, new_file_name)
    path = handle_uploaded_file(temp_path, f)
    if not path:
        return RestResponse.failure("上传失败，保存临时文件失败")

    img_file_name_list = []
    zip_dir = os.path.join(TEMP_DIR, f_name)
    try:
        if os.path.exists(zip_dir):
            shutil.rmtree(zip_dir)
            os.mkdir(zip_dir)
        # 使用zipfile解压，声明只读
        with zipfile.ZipFile(temp_path, "r") as zip_ref:

            zip_name_list = zip_ref.namelist()
            for name in zip_name_list:
                if name.startswith("__MACOSX"):
                    continue
                name_l = name.lower()
                # jpg|png|jpeg
                if name_l.endswith('.jpg') or name_l.endswith(".png") or name_l.endswith('.jpeg'):
                    img_file_name_list.append(name)
                    logging.info("解压#name = %s", name)
                    zip_ref.extract(name, zip_dir)
    except zipfile.BadZipfile or ValueError:
        if os.path.exists(zip_dir):
            shutil.rmtree(zip_dir)
        return RestResponse.failure("上传失败，解压zip文件失败")
    finally:
        # 解压后删除上传的zip文件
        if os.path.exists(temp_path) and os.path.isfile(temp_path):
            os.remove(temp_path)

    if not os.path.exists(zip_dir) or not os.listdir(zip_dir):
        return RestResponse.failure("上传失败，解压zip内容为空")

    if len(img_file_name_list) <= 0:
        if os.path.exists(zip_dir):
            shutil.rmtree(zip_dir)
        return RestResponse.failure("上传失败，解压zip不包含图片")

    # key qr_content : WaAccountQr3
    c_qr = {}
    c_qr_image = {}
    t_fm = time_utils.fmt_datetime(time_utils.get_now_bj_time(), "%Y_%m_%d")
    t_dir = f"upload/{t_fm}/"
    executor = ThreadPoolExecutor(max_workers=30)

    thread_task = []
    for img in img_file_name_list:
        i_path = os.path.join(zip_dir, img)
        if not os.path.exists(i_path):
            logging.info("遍历zip解压后的图片，不存在当前文件 path = %s", i_path)
            continue

        task = executor.submit(qr_util.get_qr_code, i_path)
        thread_task.append((i_path, task))
        logging.info("解析zip解压后的图片, path = %s", i_path)

    for i_path, t in thread_task:
        parsed = t.result()
        logging.info("线程任务完成，parsed = %s", parsed)
        if not parsed:
            continue
        db_path = t_dir + str(uuid.uuid4()) + str(os.path.splitext(name)[-1])
        logging.info("生成数据库保持的文件路径 path = %s", db_path)
        c_qr_image[parsed] = (i_path, db_path)
        data_dict = {
            'qr_content': str(parsed).strip(), 'qr_path': db_path, 'op_user_id': user_id
        }
        model = wa_service.wa_qr_create_model(back_type, **data_dict)
        if model:
            c_qr[parsed] = model

    if len(c_qr) == 0:
        if os.path.exists(zip_dir):
            shutil.rmtree(zip_dir)
        return RestResponse.failure("上传失败，可能不存在不可解析的二维码")

    c_qr_keys = list(c_qr.keys())
    # 查询已经存在的记录
    query_list = queryset.filter(qr_content__in=c_qr_keys)

    # 去掉数据库已经存在的数据
    for query in query_list:
        if c_qr_keys.index(query.qr_content) >= 0:
            qr_c = query.qr_content
            c_qr.pop(qr_c)
            c_qr_image.pop(qr_c)

    if len(c_qr) == 0:
        if os.path.exists(zip_dir):
            shutil.rmtree(zip_dir)
        return RestResponse.failure("上传失败，数据已经存在")

    db_qr_keys = list(c_qr.keys())
    db_qr_list = list(c_qr.values())
    try:
        with transaction.atomic():
            for k in db_qr_keys:
                wa_service.add_aqr_hash(k, back_type, user_id)
            queryset.bulk_create(db_qr_list)
    except Exception:
        if os.path.exists(zip_dir):
            shutil.rmtree(zip_dir)
        return RestResponse.failure("上传失败，更新数据库失败")

    # 将解压的临时图片移动到指定目录
    need_move_img_list = list(c_qr_image.values())
    for img, dst_img in need_move_img_list:
        if not os.path.exists(img) or not os.path.isfile(img):
            continue
        dst = os.path.join(MEDIA_ROOT, dst_img)
        if os.path.exists(dst):
            logging.info("将解压的临时文件移动到上传目录, 文件存在，先删除")
            os.remove(dst)

        try:
            dst_dir = os.path.dirname(dst)
            if not os.path.exists(dst_dir):
                os.mkdir(dst_dir)
            logging.info("将解压的临时文件移动到上传目录 src = %s, dst = %s", img, dst)
            shutil.move(img, dst)
        except shutil.Error or FileNotFoundError:
            pass
    if os.path.exists(zip_dir):
        shutil.rmtree(zip_dir)
    return RestResponse.success("上传成功")


@log_func
@api_op_user
def wa_qr_export_with_id(request: HttpRequest):
    ids_str = request.GET['ids']
    logging.info("export ids = %s", str(ids_str))
    if utils.str_is_null(str(ids_str)):
        logging.info("export id 失败，请选择Id")
        return HttpResponse(status=404, content="失败，请选择Id")
    ids = str(ids_str).split(',')
    if len(ids) == 0:
        logging.info("export id 失败，请选择Id")
        return HttpResponse(status=404, content="失败，请选择Id")

    user = user_dao.get_user(request)
    if not user:
        return HttpResponse(status=404, content="下载失败，需要登录")
    user_id = user.id
    back_type = request.POST['back_type'] or user.back_type
    queryset = wa_service.wa_qr_queryset(back_type)
    if not queryset:
        return HttpResponse(status=404, content=f"失败，用户类型错误 {back_type}")

    export_type = request.GET['export_type'] | request.POST['export_type']

    _status = wa_util.get_export_type(export_type)
    if _status:
        filter_field = {
            "used": _status
        }
        queryset = queryset.filter(**filter_field)

    query_list = queryset.filter(id__in=ids, op_user_id=user_id).values(
        "qr_content", 'qr_path', 'country', 'age', 'work', 'mark', 'link_mark',
        'money', "op_user__username", 'op_user__name', 'create_time'
    )

    return handle_export(query_list)


@log_func
@api_op_user
def wa_qr_export(request: HttpRequest):
    user = user_dao.get_user(request)
    if not user:
        return HttpResponse(status=404, content="下载失败，需要登录")
    user_id = user.id
    back_type = request.GET.get('back_type') or user.back_type
    queryset = wa_service.wa_qr_queryset(back_type)
    if not queryset:
        return HttpResponse(status=404, content=f"失败，用户类型错误 {back_type}")

    if request.session['user'].get('role') == USER_ROLE_ADMIN:
        # 管理员导出全部数据
        logging.info("管理员导出全部数据")
        query_list = queryset.values(
            "qr_content", 'qr_path', 'country', 'age', 'work', 'mark', 'link_mark',
            'money', "op_user__username", 'op_user__name', 'create_time'
        )
    else:
        logging.info("非管理员导出自身当天全部数据")
        start, end = time_utils.get_cur_day_time_range()
        # 非管理员导出当天数据
        query_list = queryset.filter(op_user_id=user_id, create_time__gte=start, create_time__lt=end).values(
            "qr_content", 'qr_path', 'country', 'age', 'work', 'mark', 'link_mark',
            'money', "op_user__username", 'op_user__name', 'create_time'
        )
    return handle_export(query_list)


def handle_export(query_list):
    data_size = len(query_list)
    if data_size <= 0:
        return HttpResponse(status=404, content="下载失败，没有数据")
    limit = 1000
    count = int(data_size / limit) + 1
    logging.info("handle_export # 数据大小 = %s, count = %s", data_size, count)
    file_path = None

    for index in range(0, count):
        offset = index * limit
        _next = offset + limit
        data_list = query_list[offset:_next]
        logging.info("offset = %s, next = %s size = %s", offset, _next, len(data_list))
        if len(data_list) == 0:
            break
        excel_list: List[ExcelBean] = list()
        for data in data_list:
            name = data.get('op_user__name') or data.get('op_user__username') or ""
            abs_path = os.path.join(MEDIA_ROOT, data.get('qr_path'))
            excel_list.append(
                ExcelBean(
                    qr_content=data.get('qr_content'),
                    qr_code_abs_path=abs_path,
                    country=data.get('country'),
                    age=data.get('age'),
                    work=data.get('work'),
                    mark=data.get('mark'),
                    link_mark=data.get('link_mark'),
                    money=data.get('money'),
                    op_user=name,
                    upload_time=time_utils.fmt_datetime(data.get('create_time'))
                )
            )
        logging.info("handle_export# index = %s 转换ExcelBean成功 = %s", index, len(excel_list))
        if len(excel_list) <= 0:
            continue
        if not file_path:
            temp_path = os.path.join(TEMP_DIR, "excel")
            if not os.path.exists(temp_path):
                os.mkdir(temp_path)
            logging.info("handle_export#开始生成excel文件，目录 = %s", temp_path)
            file_path = excel_util.create_excel2(excel_list, temp_path)
            if not file_path:
                return HttpResponse(status=404, content="下载失败，创建excel失败")
        else:
            logging.info("handle_export# index = %s追加生成excel文件，文件 = %s", index, file_path)
            excel_util.append_excel2(excel_list, file_path)

    logging.info("handle_export#数据填充完毕，最终文件 = %s", file_path)
    file = open(file_path, 'rb')
    file_name = os.path.basename(file_path)
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="' + escape_uri_path(file_name) + '"'
    return response


@log_func
def wa_qr_handle_dispatcher(request: HttpRequest):
    body = utils.request_body(request)
    is_all = utils.is_bool_val(body.get("isAll"))

    user = user_dao.get_user(request)
    if not user:
        return RestResponse.failure("分发错误，未登录")
    user_id = user.id
    back_type = request.POST['back_type'] or user.back_type
    queryset = wa_service.wa_qr_queryset(back_type)
    record_queryset = wa_service.wa_qr_record_queryset(back_type)
    record_type = wa_service.get_record_type(back_type)
    if not queryset or not record_queryset:
        return RestResponse.failure(f"失败，用户类型错误 {back_type}")

    try:
        code, msg = wa_service.dispatcher_aqr(queryset, back_type, record_queryset, record_type, is_all)
        if code < 0:
            return RestResponse.failure(str(msg))
        return RestResponse.success(msg)
    except BaseException as e:
        logging.info("handle_dispatcher# e = %s trace = %s", str(e), traceback.format_exc())
        return RestResponse.failure("分发错误，请联系管理员")


@log_func
def unused_list(request: HttpRequest):
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)
    dispatch_id = body.get("dispatchId")
    back_type = body.get('back_type')
    filter_args = {
        'used': UsedStatus.Default
    }
    if not utils.str_is_null(dispatch_id):
        filter_args['qr_content__contains'] = dispatch_id

    queryset = wa_service.wa_qr_queryset(back_type)
    if not queryset:
        return RestResponse.success(data=[])
    query = queryset.filter(**filter_args)
    res = query.values(
        "id", 'qr_content', 'op_user__username', 'is_bind', 'create_time'
    )[start_row:end_row]
    return RestResponse.success_list(count=query.count(), data=list(res))


def dispatch(request: HttpRequest):
    body = utils.request_body(request)
    back_type = body.get('back_type')
    if not back_type or int(back_type) not in USER_TYPES:
        return RestResponse.failure("分发错误，backType类型错误")

    user_id = body.get("user_id", "")
    aids_str = body.get("aids", "")
    aids = list(set(str(aids_str).split(",")))
    aids = [int(x.strip()) for x in aids if x.strip() != '']

    if utils.str_is_null(user_id):
        raise BusinessException.msg("参数错误，必须要有用户id")
    if utils.str_is_null(aids_str) or len(aids) == 0:
        raise BusinessException.msg("参数错误，必须要有账号数据")

    if not User.objects.filter(id=user_id).exists():
        raise BusinessException.msg("分配用户不存在")
    logging.info("WhatsApp#Qr分配#user_id = %s, aids = %s", user_id, str(aids))
    queryset = wa_service.wa_qr_queryset(back_type)
    record_query = wa_service.wa_qr_record_queryset(back_type)

    bat_record_list = []

    with transaction.atomic():
        record_query.filter(account__id__in=aids).delete()

        for qr_id in aids:
            create_dict = {
                'user_id': user_id,
                'account_id': qr_id,
                'used': UsedStatus.Default,
                'create_time': time_utils.get_now_bj_time_str(),
                'update_time': time_utils.get_now_bj_time_str()
            }
            model = wa_service.wa_qr_record_create_model(back_type, **create_dict)
            if model:
                bat_record_list.append(model)
            else:
                logging.info(f"{back_type}#add_record_id 失败，创建model为空")

        record_query.bulk_create(bat_record_list)

        ids = list(map(lambda x: x.account_id, bat_record_list))
        logging.info(f"{back_type}#将数据 bind 设置为True ids = %s", ids)
        queryset.filter(id__in=ids).update(is_bind=True)

    return RestResponse.success(msg="分配完成")


@log_func
def update_bind(request: HttpRequest):
    body = utils.request_body(request)
    aid = body.get("id")
    bind = body.get("bind")
    back_type = body.get('back_type')
    if not back_type or int(back_type) not in USER_TYPES:
        raise BusinessException.msg("分发错误，backType类型错误")
    if utils.str_is_null(aid):
        raise BusinessException.msg("修改失败，id错误")
    if not utils.is_bool(bind):
        raise BusinessException.msg("修改失败，状态异常")
    queryset = wa_service.wa_qr_queryset(back_type)
    record_query = wa_service.wa_qr_record_queryset(back_type)

    if not queryset or not record_query:
        raise BusinessException.msg("修改失败，查询错误")

    bind_val = utils.is_bool_val(bind)

    with transaction.atomic():
        logging.info("waqr#修改绑定状态为%s", bind_val)
        queryset.filter(id=aid).update(is_bind=bind_val)
        if not bind_val:
            logging.info("waqr#修改绑定状态为false，删除绑定记录")
            record_query.filter(account_id=aid).delete()
        return RestResponse.success("修改成功", data=bind_val)


@log_func
def handle_used_state(request: HttpRequest):
    body = utils.request_body(request)
    logging.info("批量修改使用状态#waw_qr#body = %s", str(body))
    user = user_dao.get_user(request)
    if not user:
        return RestResponse.failure("分发错误，未登录")
    back_type = request.POST['back_type']
    queryset = wa_service.wa_qr_queryset(back_type)
    record_queryset = wa_service.wa_qr_record_queryset(back_type)
    if not queryset or not record_queryset:
        return RestResponse.failure(f"失败，用户类型错误 {back_type}")
    try:
        ids = body.get("ids", "")
        ids = ids.split(",")
        used = body.get('used')
        used = utils.get_status(used)
        queryset.filter(id__in=ids).update(used=used)
        record_queryset.filter(account__id__in=ids).update(used=used)
        return RestResponse.success()
    except BaseException as e:
        logging.info("批量修改使用状态失败 %s => %s", str(e), traceback.format_exc())
        return RestResponse.failure("批量修改失败")
