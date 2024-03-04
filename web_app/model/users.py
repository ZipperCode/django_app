from django.db import models

USER_ROLE_ADMIN = 0
USER_ROLE_UPLOADER = 1
USER_ROLE_BUSINESS = 2

ROLE_CHOOSE = (
    (USER_ROLE_ADMIN, u"管理员"),
    (USER_ROLE_UPLOADER, u"粉端账号"),
    (USER_ROLE_BUSINESS, u"业务员"),
)

USER_BACK_TYPE_NONE = 0
USER_BACK_TYPE_LINE = 1
USER_BACK_TYPE_WA = 2
USER_BACK_TYPE_WA2 = 3
USER_BACK_TYPE_WA3 = 4
USER_BACK_TYPE_WA4 = 5
USER_BACK_TYPE_WA5 = 6
USER_BACK_TYPE_WA6 = 7
USER_BACK_TYPE_WA7 = 8
USER_BACK_TYPE_LINE_PAIR = 9

USER_TYPES = (USER_BACK_TYPE_LINE, USER_BACK_TYPE_WA,
              USER_BACK_TYPE_WA2, USER_BACK_TYPE_WA3,
              USER_BACK_TYPE_WA4, USER_BACK_TYPE_WA5,
              USER_BACK_TYPE_WA6, USER_BACK_TYPE_WA7,
              USER_BACK_TYPE_LINE_PAIR
              )

WA_TYPES = (USER_BACK_TYPE_WA,
            USER_BACK_TYPE_WA2, USER_BACK_TYPE_WA3,
            USER_BACK_TYPE_WA4, USER_BACK_TYPE_WA5,
            USER_BACK_TYPE_WA6, USER_BACK_TYPE_WA7,
            )

LINE_TYPES = (USER_BACK_TYPE_LINE, USER_BACK_TYPE_LINE_PAIR)

USER_BACK_TYPE = (
    (USER_BACK_TYPE_NONE, u'无类型'),
    (USER_BACK_TYPE_LINE, u"Line类型"),
    (USER_BACK_TYPE_WA, u"WhatsApp类型"),
    (USER_BACK_TYPE_WA2, u"WhatsApp2类型"),
    (USER_BACK_TYPE_WA3, u"WhatsApp3类型"),
    (USER_BACK_TYPE_WA4, u"WhatsApp4类型"),
    (USER_BACK_TYPE_WA5, u"WhatsApp5类型"),
    (USER_BACK_TYPE_WA6, u"WhatsApp6类型"),
    (USER_BACK_TYPE_WA7, u"WhatsApp7类型"),
    (USER_BACK_TYPE_LINE_PAIR, u"LinePair"),
)


class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField("用户名", max_length=255, null=False, unique=True)
    password = models.CharField("密码", max_length=64, null=False)
    is_admin = models.BooleanField("是否管理员", default=False)
    role = models.IntegerField("用户角色", choices=ROLE_CHOOSE, default=2)
    name = models.CharField("显示的名称", max_length=255, null=True)
    back_type = models.IntegerField("后台类型", choices=USER_BACK_TYPE, default=USER_BACK_TYPE_NONE)
    bind_dispatch = models.BooleanField("是否禁用分配", default=False)
    create_time = models.DateTimeField("创建时间", null=True, auto_now_add=True)
    update_time = models.DateTimeField("更新时间", null=True, auto_now=True)


RECORD_TYPE_NONE = 0
RECORD_TYPE_LINE_ID = 1
RECORD_TYPE_LINE_QR = 2
RECORD_TYPE_WA_ID = 3
RECORD_TYPE_WA_QR = 4
RECORD_TYPE_WA_ID2 = 5
RECORD_TYPE_WA_QR2 = 6

RECORD_TYPE_WA_ID3 = 7
RECORD_TYPE_WA_QR3 = 8

RECORD_TYPE_WA_ID4 = 9
RECORD_TYPE_WA_QR4 = 10

RECORD_TYPE_WA_ID5 = 11
RECORD_TYPE_WA_QR5 = 12

RECORD_TYPE_WA_ID6 = 13
RECORD_TYPE_WA_QR6 = 14

RECORD_TYPE_WA_ID7 = 15
RECORD_TYPE_WA_QR7 = 16

USER_RECORD_TYPE = (
    (RECORD_TYPE_NONE, u"无类型"),
    (RECORD_TYPE_LINE_ID, u"LinesID"),
    (RECORD_TYPE_LINE_QR, u"LinesQR"),
    (RECORD_TYPE_WA_ID, u"WhatsAppID"),
    (RECORD_TYPE_WA_QR, u"WhatsAppQR"),
    (RECORD_TYPE_WA_ID2, u"WhatsAppID2"),
    (RECORD_TYPE_WA_QR2, u"WhatsAppQR2"),
    (RECORD_TYPE_WA_ID3, u"WhatsAppID3"),
    (RECORD_TYPE_WA_QR3, u"WhatsAppQR3"),
    (RECORD_TYPE_WA_ID4, u"WhatsAppID4"),
    (RECORD_TYPE_WA_QR4, u"WhatsAppQR4"),
    (RECORD_TYPE_WA_ID5, u"WhatsAppID5"),
    (RECORD_TYPE_WA_QR5, u"WhatsAppQR5"),

    (RECORD_TYPE_WA_ID6, u"WhatsAppID6"),
    (RECORD_TYPE_WA_QR6, u"WhatsAppQR6"),

    (RECORD_TYPE_WA_ID7, u"WhatsAppID7"),
    (RECORD_TYPE_WA_QR7, u"WhatsAppQR7"),
)


class UserAccountRecord(models.Model):
    """
    保存用户的当天分配数据
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(to="User", verbose_name="用户外键", null=True, on_delete=models.SET_NULL)
    data_num = models.IntegerField("当天数量", default=0)
    type = models.IntegerField("数据类型", choices=USER_RECORD_TYPE, default=RECORD_TYPE_NONE)
    create_time = models.DateTimeField("创建时间", null=True, auto_now_add=True)
    update_time = models.DateTimeField("更新时间", null=True, auto_now=True)


# MENU_TYPE_NONE = 0
# MENU_TYPE_LINE = 1
# MENU_TYPE_WA = 2
# MENU_TYPE_WA2 = 3
# MENU_TYPE_WA3 = 4
# MENU_TYPE_WA4 = 5
# MENU_TYPE_WA5 = 6
#
# MENU_CHOICES = (
#     (MENU_TYPE_LINE, u"line"),
#     (MENU_TYPE_WA, u"wa"),
#     (MENU_TYPE_WA2, u"wa2"),
#     (MENU_TYPE_WA3, u"wa3"),
#     (MENU_TYPE_WA4, u"wa4"),
#     (MENU_TYPE_WA5, u"wa5"),
# )


class UserMenu(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(to="User", verbose_name="用户外键", null=True, on_delete=models.SET_NULL)
    # 扩展 back_type 让用户支持展示更多菜单
    menu_type = models.IntegerField("菜单类型", null=True, choices=USER_BACK_TYPE, default=USER_BACK_TYPE_NONE)
    create_time = models.DateTimeField("创建时间", null=True, auto_now_add=True)
    update_time = models.DateTimeField("更新时间", null=True, auto_now=True)
