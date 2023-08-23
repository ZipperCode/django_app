from django.db import models

from base.db.BaseModel import BaseModel, RowMixin

GENDER_CHOICES = (
    (0, ""),
    (1, "男"),
    (2, "女"),
)


class OperatorMixin(models.Model):
    creator = models.ForeignKey(to="User", related_query_name='creator_query', null=True,
                                verbose_name='创建人', on_delete=models.SET_NULL, db_constraint=False)
    modifier = models.CharField("修改人", max_length=100, null=True, blank=True)

    class Meta:
        abstract = True


class User(BaseModel, RowMixin):
    username = models.CharField("用户名", max_length=100, unique=True, db_index=True)
    password = models.CharField("密码", max_length=32, null=False)
    avatar = models.CharField("头像", max_length=200, null=True, blank=True)
    name = models.CharField("姓名", max_length=40)
    gender = models.SmallIntegerField("性别", choices=GENDER_CHOICES, null=True, blank=True, default=0)
    IDENTITY_CHOICES = (
        (0, "超级管理员"),
        (1, "用户"),
    )
    identity = models.SmallIntegerField("身份标识", choices=IDENTITY_CHOICES, null=True, blank=True, default=1)

    class Meta:
        db_tablespace = 'common'
        verbose_name = "用户表"


class Menu(BaseModel, RowMixin):
    parent = models.ForeignKey("Menu", on_delete=models.CASCADE, null=True, blank=True, db_constraint=False,
                               verbose_name="上级菜单")
    icon = models.CharField("菜单图标", null=True, blank=True, max_length=100)
    title = models.CharField("菜单标题", max_length=100)
    path = models.CharField("路由地址", max_length=128, null=True, blank=True)
    sort = models.IntegerField("排序", default=0, null=True, blank=True)

    component = models.CharField("组件路径", max_length=128, null=True, blank=True)

    grant_button = models.BooleanField("是否可配置按钮权限", default=False)
    visible = models.BooleanField("是否在侧边栏可见", default=True)

    class Meta:
        db_tablespace = "common"
        verbose_name = "菜单表"
        ordering = ('sort',)


class Button(BaseModel, RowMixin):
    name = models.CharField(max_length=64, verbose_name="权限名称", help_text="权限名称")
    value = models.CharField(max_length=64, verbose_name="权限值", help_text="权限值")

    class Meta:
        db_tablespace = "common"
        verbose_name = '权限标识表'
        ordering = ('-name',)


class MenuButton(BaseModel, RowMixin):
    menu = models.ForeignKey(Menu, verbose_name="关联菜单", on_delete=models.CASCADE, db_constraint=False)
    name = models.CharField(max_length=64, verbose_name="名称", help_text="名称")
    value = models.CharField(max_length=64, verbose_name="权限值", help_text="权限值")
    api = models.CharField(max_length=64, verbose_name="接口地址", help_text="接口地址")
    METHOD_CHOICES = (
        (0, "GET"),
        (1, "POST"),
        (2, "PUT"),
        (3, "DELETE"),
    )
    method = models.SmallIntegerField(default=0, verbose_name="接口请求方法", null=True, blank=True,
                                      help_text="接口请求方法")

    class Meta:
        db_tablespace = "common"
        verbose_name = "按钮表"
