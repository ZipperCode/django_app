import enum

from django.db import models


class UsedStatus(models.IntegerChoices):
    # 未使用
    Default = 0
    # 已使用
    Used = 1
    # 不可用
    Unable = 2
