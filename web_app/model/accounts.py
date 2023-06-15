from django.db import models

from util import utils


class AccountId(models.Model):
    id = models.AutoField(primary_key=True)
    account_id = models.CharField("ID", max_length=255, null=False, unique=True)
    country = models.CharField("国家", max_length=100, null=True)
    age = models.IntegerField("年龄", default=0)
    work = models.CharField("工作", max_length=255, null=True, default="无")
    # 最大10位，保留两位小数
    money = models.DecimalField("收入", default=0.0, max_digits=10, decimal_places=2)
    mark = models.TextField("备注", null=True)
    op_user = models.ForeignKey("User", null=True, on_delete=models.SET_NULL)
    create_time = models.DateTimeField("创建时间（上传时间）", null=True, auto_now_add=True)
    update_time = models.DateTimeField("更新时间", null=True, auto_now=True)

    @property
    def op_user_name(self):
        op_u = self.op_user
        op_name = op_u.username
        if not utils.str_is_null(op_u.name):
            op_name = op_u.name
        return op_name


class AccountQr(models.Model):
    id = models.AutoField(primary_key=True)
    qr_content = models.TextField("二维码内容", unique=True)
    # 图片上传后保存到一个目录中，后续就根据路径去拿图片
    qr_path = models.FileField("二维码图片路径", null=True, max_length=255, upload_to="data/upload/%Y_%m_%d/")
    country = models.CharField("国家", max_length=100, null=True)
    age = models.IntegerField("年龄", default=0)
    work = models.CharField("工作", max_length=255, null=True, default="无")
    # 最大10位，保留两位小数
    money = models.DecimalField("收入", default=0.0, max_digits=10, decimal_places=2)
    mark = models.TextField("备注", null=True)
    op_user = models.ForeignKey("User", null=True, on_delete=models.SET_NULL)
    create_time = models.DateTimeField("创建时间（上传时间）", null=True, auto_now_add=True)
    update_time = models.DateTimeField("更新时间", null=True, auto_now=True)
