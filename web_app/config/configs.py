import logging
import traceback
from hashlib import md5

import pymysql
from django.apps import AppConfig

pymysql.install_as_MySQLdb()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class InitConfig(AppConfig):
    name = 'web_app'

    def ready(self):
        logging.info(">>>>>>>>>>>>ready")
        print("init ready")
        try:
            from web_app.model.users import User
            from web_app.model.users import USER_ROLE_ADMIN, USER_ROLE_SUPER_ADMIN
            if not User.objects.filter(username='admin').exists():
                User.objects.create(
                    username='admin',
                    password=md5("admin".encode()).digest().hex().lower(),
                    is_admin=True,
                    name="Admin",
                    role=USER_ROLE_SUPER_ADMIN
                )
            else:
                User.objects.filter(username='admin').update(role=USER_ROLE_SUPER_ADMIN)
        except BaseException:
            logging.info("append excel fail = %s", traceback.format_exc())
