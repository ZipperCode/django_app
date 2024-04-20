from django.db import models

from web_app.model.const import UsedStatus
from web_app.model.users import User


class AccountLink(models.Model):
    id = models.AutoField(primary_key=True)
    link = models.CharField("链接", max_length=1000, null=False, unique=True)
    remark = models.CharField("备注", max_length=255, null=True, blank=True)
    op_user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    used = models.SmallIntegerField("是否使用", default=UsedStatus.Default, choices=UsedStatus.choices)
    create_time = models.DateTimeField("创建时间", null=True, auto_now_add=True)
    update_time = models.DateTimeField("更新时间", null=True, auto_now=True)
