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

USER_BACK_TYPE = (
    (USER_BACK_TYPE_NONE, u'无类型'),
    (USER_BACK_TYPE_LINE, u"Line类型"),
    (USER_BACK_TYPE_WA, u"WhatsApp类型")
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

USER_RECORD_TYPE = (
    (RECORD_TYPE_NONE, u"无类型"),
    (RECORD_TYPE_LINE_ID, u"LinesID"),
    (RECORD_TYPE_LINE_QR, u"LinesQR"),
    (RECORD_TYPE_WA_ID, u"WhatsAppID"),
    (RECORD_TYPE_WA_QR, u"WhatsAppQR"),
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
