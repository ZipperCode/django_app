import enum

from django.db import models


class UsedStatus(models.IntegerChoices):
    Default = 0
    Used = 1
    Unable = 2
