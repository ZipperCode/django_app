import logging

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
        # try:
        #     import web_app.service.wa_service
        #     web_app.service.wa_service.sync_id_hash()
        #     web_app.service.wa_service.sync_qr_hash()
        #     web_app.service.wa_service.sync_used_id()
        #     web_app.service.wa_service.sync_used_qr()
        # except:
        #     pass
