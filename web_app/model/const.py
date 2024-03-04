import enum

from django.db import models


class UsedStatus(models.IntegerChoices):
    # 未使用
    Default = 0
    # 已使用
    Used = 1
    # 不可用
    Unable = 2


class LineClassify(models.IntegerChoices):
    # line
    Line = 0
    # pairs
    Pairs = 1
