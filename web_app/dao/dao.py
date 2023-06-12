from typing import Optional, List

from django.db.models import Q

import util.utils
from util import utils
from web_app.models import ContactUser, ContactInfo


# def insert_user(phone: str, code: Optional[str]):
#     q = Q(user_phone=phone) | Q(code=code)
#     res = ContactUser.objects.filter(q)
#     if res.count() > 0:
#         return res.first().id
#     return ContactUser.objects.create(user_phone=phone, code=code).id
#
#
# def insert_contact(contact_user_id: int, contact_list: List[dict]):
#     if len(contact_list) <= 0:
#         return
#     res = ContactUser.objects.filter(id=contact_user_id).first()
#     if res is None or res.id <= 0:
#         return
#     contact_info_list = list()
#
#     for contact in contact_list:
#         name = contact.get("name")
#         if util.utils.str_is_null(str(name)):
#             continue
#         phone = contact.get('phone')
#         if util.utils.str_is_null(str(phone)):
#             continue
#
#         contact_info_list.append(ContactInfo(ref_contact_id=contact_user_id, name=name, phone=phone))
#
#     ContactInfo.objects.bulk_create(contact_info_list)
#
#
# def contact_user_list(start_row, end_row) -> tuple:
#     query = ContactUser.objects
#     res = query.all()[start_row: end_row]
#     count = query.count()
#     return utils.model2json(res), count
#
#
# def contact_info_list(contact_user_id) -> list:
#     res = ContactInfo.objects.filter(ref_contact_id=contact_user_id)
#     if res.count() == 0:
#         return list()
#     return utils.model2json(res)
