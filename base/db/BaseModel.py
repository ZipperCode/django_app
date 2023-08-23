from django.db import models

from apps import common

STATUS_CHOICES = (
    (0, "禁用"),
    (1, "启用")
)


class RowMixin(models.Model):
    status = models.SmallIntegerField("数据状态", choices=STATUS_CHOICES, null=True, blank=True, default=1)
    is_delete = models.BooleanField("是否逻辑删除", default=False)

    class Meta:
        abstract = True


class BaseModel(models.Model):
    id = models.AutoField(primary_key=True)

    create_time = models.DateTimeField("创建时间", auto_created=True)
    update_time = models.DateTimeField("更新时间", auto_created=True, auto_now=True)

    class Meta:
        abstract = True
