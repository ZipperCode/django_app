import os
import shutil
import datetime

SELF = os.path.abspath(__file__)
BASE_PATH = os.path.dirname(SELF)


def yesterday():
    today = datetime.date.today()
    oneday = datetime.timedelta(days=1)
    yesterday = today-oneday
    return yesterday.strftime("%Y-%m-%d")


for each in os.listdir(BASE_PATH):
    path = os.path.join(BASE_PATH, each)
    if os.path.isdir(path):
        run_log = os.path.join(path, "compose/uwsgi/django_app-uwsgi.log")
        if os.path.exists(run_log):
            yesterday_log = os.path.join(path, "django_app-uwsgi_" + yesterday() + ".log")
            shutil.move(run_log, yesterday_log)

with open(SELF, "rb+") as file:
    all = file.read()
    file.seek(0, 0)
    file.write(all)