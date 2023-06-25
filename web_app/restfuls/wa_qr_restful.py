import datetime
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
from web_app.dao import wa_dao, user_dao
from web_app.decorators.admin_decorator import log_func, api_op_user, op_admin
from web_app.decorators.restful_decorator import api_post
from web_app.model.users import User, USER_ROLE_ADMIN, USER_ROLE_BUSINESS
from web_app.model.wa_accounts import WaUserQrRecord, WaAccountQr
from web_app.settings import BASE_DIR, MEDIA_ROOT
from web_app.util import rest_list_util

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TEMP_DIR = os.path.join(BASE_DIR, "data", 'temp')


@log_func
@api_op_user
def account_qr_list(request: HttpRequest):
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.failure("获取信息失败，用户未登录")

    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)
    res, count = wa_dao.search_account_qr_page(body, start_row, end_row, user)
    return RestResponse.success_list(count=count, data=res)


@log_func
def business_list(request: HttpRequest):
    user = user_dao.get_user(request)
    if user is None or not isinstance(user, User):
        return RestResponse.success_list(count=0, data=[])
    start_row, end_row = utils.page_query(request)
    body = utils.request_body(request)

    # 查询记录
    start_t, end_t = time_utils.get_cur_day_time_range()
    q = Q(create_time__gte=start_t, create_time__lt=end_t) | Q(used=False)

    record_ids = list(
        map(
            lambda x: x.get('account_id'),
            list(
                WaUserQrRecord.objects.filter(user_id=user.id).filter(q).distinct()
                .order_by('user_id', 'account_id').values('account_id')
            )
        )
    )

    if len(record_ids) == 0:
        logging.info("当前用户没有可分配的数据，返回空数据")
        return RestResponse.success_list(count=0, data=[])

    logging.info("当前用户所分配的ids = %s", record_ids)

    query = rest_list_util.search_account_common_field(WaAccountQr.objects, body)
    query = query.filter(id__in=record_ids)
    res = list(
        query.values(
            'id', 'qr_content', 'qr_path', 'country', 'age', 'work', 'money', 'mark', 'used',
            'op_user__username', 'create_time', 'update_time'
        )[start_row: end_row]
    )
    res, count = list(res), query.count()
    return RestResponse.success_list(count=count, data=res)


@log_func
def dispatch_record_list(request: HttpRequest):
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
    query = WaUserQrRecord.objects.filter(user__isnull=False, account__isnull=False)
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


def account_qr_add(request: HttpRequest):
    body = utils.request_body(request)
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

    WaAccountQr.objects.create(
        qr_content=qr_content, qr_path=qr, country=country, age=age,
        work=work, money=money, mark=mark,
        op_user_id=user.id
    )

    return RestResponse.success("添加成功")


@api_post
@api_op_user
def account_qr_update(request: HttpRequest):
    body = utils.request_body(request)
    logging.info("qr_update# body = %s", str(body))
    db_id = body.get('id', "")
    country = body.get("country", "")
    age = body.get("age", 0)
    work = body.get("work", "")
    money = body.get('money', 0.0)
    mark = body.get('mark', "")
    used = body.get('used')
    if utils.str_is_null(db_id) or not utils.is_int(db_id):
        return RestResponse.failure("修改失败，id不能为空或只能数字")

    user_id = request.session.get('user_id')
    if not user_id or utils.str_is_null(user_id):
        return RestResponse.failure("修改失败，未获取到登录用户信息")

    query = WaAccountQr.objects.filter(id=db_id)
    if not query.exists():
        return RestResponse.failure("修改失败，记录不存在")
    role = request.session.get('user').get('role')
    is_business_user = role == USER_ROLE_BUSINESS
    is_admin = role == USER_ROLE_ADMIN
    upd_field = {
        "country": country, "age": age,
        "work": work, "money": money, "mark": mark,
        "update_time": time_utils.get_now_bj_time()
    }
    with transaction.atomic():
        if is_admin and not utils.str_is_null(used):
            logging.info("管理员编辑，且数据的状态为 %s, 修改", used)
            _status = utils.is_bool_val(used)
            upd_field['used'] = _status
            if not _status:
                logging.info("管理员编辑为不使用")
                _q = WaUserQrRecord.objects.filter(account_id=db_id)
                if _q.exists():
                    _q.update(used=False)
            else:
                # 修改is_bind=True，分发的时候就过滤这个了
                upd_field['is_bind'] = True
        elif is_business_user:
            logging.info("业务员编辑, 直接修改为已使用")
            upd_field['used'] = True
            _q = WaUserQrRecord.objects.filter(user_id=user_id, account_id=db_id)
            if _q.exists():
                _q.update(used=True)

        query.update(**upd_field)

    return RestResponse.success("更新成功")


@log_func
@op_admin
def account_qr_del(request: HttpRequest):
    if request.method != "POST":
        return RestResponse.failure("must use post")

    body = utils.request_body(request)
    id_ = body.get('id', "")
    logging.info("account_qr_del#id_ = %s", id_)
    if utils.str_is_null(id_) or not utils.is_int(id_):
        return RestResponse.failure("删除失败，id不能为空或只能数字")

    WaAccountQr.objects.filter(id=id_).delete()
    return RestResponse.success("删除成功")


@log_func
@api_op_user
def account_qr_upload(request: HttpRequest):
    f = request.FILES["image"]
    filename = request.POST["filename"]
    if not f:
        return HttpResponse("上传失败，数据传输异常")

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

    query = WaAccountQr.objects.filter(qr_content=str(parsed).strip(), op_user__isnull=False)
    if query.exists():
        return RestResponse.failure("上传失败，二维码已经存在")

    WaAccountQr.objects.create(
        qr_content=str(parsed).strip(),
        qr_path=f,
        op_user_id=user_id
    )
    return RestResponse.success("上传成功")


@log_func
@api_op_user
def account_qr_batch_upload(request: HttpRequest):
    f = request.FILES["file"]
    if not f:
        return HttpResponse("上传失败，数据传输异常")

    user_id = request.session.get('user_id')
    if not user_id or utils.str_is_null(user_id):
        return RestResponse.failure("上传失败，未获取到登录用户信息")
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

    if not os.path.exists(zip_dir) or not os.listdir(zip_dir):
        return RestResponse.failure("上传失败，解压zip内容为空")

    if len(img_file_name_list) <= 0:
        if os.path.exists(zip_dir):
            shutil.rmtree(zip_dir)
        return RestResponse.failure("上传失败，解压zip不包含图片")

    # key qr_content : WaAccountQr
    c_qr = {}
    c_qr_image = {}
    t_fm = time_utils.fmt_datetime(datetime.datetime.strptime(time_utils.get_now_bj_time()), "%Y_%m_%d")
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
        c_qr[parsed] = WaAccountQr(qr_content=str(parsed).strip(), qr_path=db_path, op_user_id=user_id)

    if len(c_qr) == 0:
        if os.path.exists(zip_dir):
            shutil.rmtree(zip_dir)
        return RestResponse.failure("上传失败，可能不存在不可解析的二维码")

    c_qr_keys = list(c_qr.keys())
    # 查询已经存在的记录
    query_list = WaAccountQr.objects.filter(qr_content__in=c_qr_keys)

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

    db_qr_list = list(c_qr.values())
    try:
        WaAccountQr.objects.bulk_create(db_qr_list)
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
def account_qr_export_with_id(request: HttpRequest):
    ids_str = request.GET['ids']
    logging.info("export ids = %s", str(ids_str))
    if utils.str_is_null(str(ids_str)):
        logging.info("export id 失败，请选择Id")
        return HttpResponse(status=404, content="失败，请选择Id")
    ids = str(ids_str).split(',')
    if len(ids) == 0:
        logging.info("export id 失败，请选择Id")
        return HttpResponse(status=404, content="失败，请选择Id")
    user_id = request.session.get('user_id')
    if not user_id or utils.str_is_null(user_id):
        logging.info("export id 失败，需要登录")
        return HttpResponse(status=404, content="下载失败，需要登录")

    query_list = WaAccountQr.objects.filter(id__in=ids, op_user_id=user_id).all()
    return handle_export(query_list)


@log_func
@api_op_user
def account_qr_export(request: HttpRequest):
    user_id = request.session.get('user_id')
    if not user_id or utils.str_is_null(user_id):
        logging.info("export id 失败，需要登录")
        return HttpResponse(status=404, content="下载失败，需要登录")

    if request.session['user'].get('role') == USER_ROLE_ADMIN:
        # 管理员导出全部数据
        logging.info("管理员导出全部数据")
        query_list = WaAccountQr.objects.all()
    else:
        logging.info("非管理员导出自身当天全部数据")
        start, end = time_utils.get_cur_day_time_range()
        # 非管理员导出当天数据
        query_list = WaAccountQr.objects.filter(op_user_id=user_id, create_time__gte=start, create_time__lt=end).all()
    return handle_export(query_list)


def handle_export(query_list):
    excel_bean_list: List[ExcelBean] = list()
    for query in query_list:
        abs_path = os.path.join(MEDIA_ROOT, query.qr_path.path)
        excel_bean_list.append(
            ExcelBean(
                qr_content=query.qr_content,
                qr_code_abs_path=abs_path,
                country=query.country,
                age=query.age,
                work=query.work,
                mark=query.mark,
                money=query.money,
                op_user=query.op_username,
                upload_time=time_utils.fmt_datetime(query.create_time)
            )
        )

    logging.info("导出内容，创建excelBean len = %s", len(excel_bean_list))
    if len(excel_bean_list) == 0:
        logging.info("export id 失败，没有对应数据")
        return HttpResponse(status=404, content="下载失败，没有对应数据")

    temp_path = os.path.join(TEMP_DIR, "excel")
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)
    file_path = excel_util.create_excel2(excel_bean_list, temp_path)
    logging.info("export_qr#生成excel文件，文件 = %s", file_path)
    if not file_path:
        logging.info("export id 失败，创建excel失败")
        return HttpResponse(status=404, content="下载失败，创建excel失败")
    logging.info('export qr#path = %s', file_path)
    file = open(file_path, 'rb')
    file_name = os.path.basename(file_path)
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="' + escape_uri_path(file_name) + '"'
    return response


@log_func
def handle_dispatcher(request: HttpRequest):
    body = utils.request_body(request)
    is_all = utils.is_bool_val(body.get("isAll"))
    try:
        code, msg = wa_dao.dispatcher_account_qr(is_all)
        if code < 0:
            return RestResponse.failure(str(msg))
        return RestResponse.success(msg)
    except BaseException as e:
        logging.info("handle_dispatcher# e = %s trace = %s", str(e), traceback.format_exc())
        return RestResponse.failure("分发错误，请联系管理员")
