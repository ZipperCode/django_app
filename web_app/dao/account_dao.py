import logging

from util import utils
from util.time_utils import convert_date
from web_app.decorators.admin_decorator import log_func
from web_app.model.accounts import AccountId, AccountQr
from web_app.model.users import User

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)


def search_account_id_page(body, start_row, end_row, user: User):
    a_id = body.get('account_id')
    country = body.get("country")
    mark = body.get("mark")
    date_start = body.get('date_start')
    date_end = body.get('date_end')
    op_user_id = body.get("op_user_select")
    logging.info("account_id_list#user.username = %s", user.username)
    logging.info("account_id_list#a_id = %s", a_id)
    logging.info("account_id_list#country = %s", country)
    logging.info("account_id_list#date_start = %s", date_start)
    logging.info("account_id_list#date_end = %s", date_end)
    logging.info("account_id_list#op_user_id = %s", op_user_id)

    if not utils.str_is_null(a_id):
        logging.info("account_id_list#id不为空直接查找id")
        query = AccountId.objects.filter(account_id=a_id).values()[start_row: end_row]
        return list(query), query.count()

    query = AccountId.objects.filter(op_user_id=user.id)

    if not utils.str_is_null(country):
        query = query.filter(country__contains=country)

    if not utils.str_is_null(mark):
        query = query.filter(mark__contains=mark)

    if not utils.str_is_null(date_start):
        start = convert_date(date_start)
        if start is not None:
            query = query.filter(create_time__gte=start)
    if not utils.str_is_null(date_end):
        end = convert_date(date_end)
        if end is not None:
            query = query.filter(create_time__lt=end)

    if utils.is_int(op_user_id):
        query = query.filter(op_user_id=op_user_id)
    res = list(
        query.values('id', 'account_id', 'country', 'age', 'work', 'money', 'mark',
                     'op_user__username', 'create_time', 'update_time'))[start_row: end_row]

    return list(res), query.count()


@log_func
def search_account_qr_page(body, start_row, end_row, user_id):
    country = body.get("country")
    mark = body.get("mark")
    date_start = body.get('date_start')
    date_end = body.get('date_end')
    op_user_id = body.get("op_user_select")
    logging.info("account_id_list#country = %s", country)
    logging.info("account_id_list#date_start = %s", date_start)
    logging.info("account_id_list#date_end = %s", date_end)
    logging.info("account_id_list#op_user_id = %s", op_user_id)

    query = AccountQr.objects.filter(op_user_id=user_id)

    if not utils.str_is_null(country):
        query = query.filter(country__contains=country)
    if not utils.str_is_null(mark):
        query = query.filter(mark__contains=country)
    if not utils.str_is_null(date_start):
        start = convert_date(date_start)
        if start is not None:
            query = query.filter(create_time__gte=start)
    if not utils.str_is_null(date_end):
        end = convert_date(date_end)
        if end is not None:
            query = query.filter(create_time__lt=end)

    if utils.is_int(op_user_id):
        query = query.filter(op_user_id=op_user_id)
    res = list(
        query.values(
            'id', 'qr_content', 'qr_path', 'country', 'age', 'work', 'money', 'mark',
            'op_user__username', 'create_time', 'update_time'
        )
    )[start_row: end_row]

    return list(res), query.count()
