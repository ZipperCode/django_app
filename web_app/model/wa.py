from django.db import models

from web_app.model.users import USER_BACK_TYPE, USER_BACK_TYPE_NONE


class WaIdHash(models.Model):
    id = models.AutoField(primary_key=True)
    id_hash = models.CharField("IDHash", max_length=32, null=False, unique=True)
    account_id = models.CharField("ID", max_length=255)
    back_type = models.IntegerField("后台类型", choices=USER_BACK_TYPE, default=USER_BACK_TYPE_NONE)
    op_user = models.ForeignKey("User", null=True, on_delete=models.SET_NULL)
    create_time = models.DateTimeField("创建时间（上传时间）", null=True, auto_now_add=True)


class WaQrHash(models.Model):
    id = models.AutoField(primary_key=True)
    id_hash = models.CharField("IDHash", max_length=32, null=False, unique=True)
    account_qr = models.CharField("qrContent", max_length=255)
    back_type = models.IntegerField("后台类型", choices=USER_BACK_TYPE, default=USER_BACK_TYPE_NONE)
    op_user = models.ForeignKey("User", null=True, on_delete=models.SET_NULL)
    create_time = models.DateTimeField("创建时间（上传时间）", null=True, auto_now_add=True)

