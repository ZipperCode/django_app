from django.db import models


class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField("用户名", max_length=255, null=False, unique=True)
    password = models.CharField("密码", max_length=64, null=False)
    is_admin = models.BooleanField("是否管理员", default=False)
    name = models.CharField("显示的名称", max_length=255, null=True)
    create_time = models.DateTimeField("创建时间", null=True, auto_now_add=True)
    update_time = models.DateTimeField("更新时间", null=True, auto_now=True)




