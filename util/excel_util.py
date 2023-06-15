import dataclasses
from typing import List, Optional

from openpyxl.workbook import Workbook

from web_app.model.accounts import AccountId

@dataclasses
class ExcelBean:
    no: int
    id: str
    country: Optional[str]
    age: int = 0
    work: Optional[str]
    money: float
    op_user: str
    upload_time: str


def create_excel(in_data_list: List[AccountId], out_path):
    book = Workbook()
    sheet = book.active
    sheet.append(['编号', 'ID', '城市', '年龄', '工作', '收入', '备注', '操作人', '上传时间'])

    for d in in_data_list:
        # row = [d.id, d.account_id, d.country, d.age, d.work, d.money, d.mark, d.]
        pass

    pass


if __name__ == '__main__':
    data_list = []
    pass
