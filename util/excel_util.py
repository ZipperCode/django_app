import logging
from dataclasses import dataclass
import os.path
import time
from typing import List, Optional

from openpyxl.styles import Font
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet


@dataclass
class ExcelBean:
    id: str
    qr_code: str = None
    qr_content: str = None
    country: Optional[str] = None
    age: int = 0
    work: Optional[str] = None
    mark: Optional[str] = None
    money: float = 0.0
    op_user: str = "None"
    upload_time: str = "2023-1-1"


def create_excel(in_data_list: List[ExcelBean], out_dir):
    try:
        book = Workbook()
        sheet: Optional[Worksheet] = book.active
        sheet.append(['ID', '城市', '年龄', '工作', '收入', '备注', '操作人', '上传时间'])
        r = sheet.row_dimensions[1]
        r.font = Font(bold=True)
        now = time.strftime("%Y-%m-%d-%H_%M_%S", time.localtime(time.time()))
        filename = os.path.join(out_dir, now + "_id.xlsx")
        for d in in_data_list:
            row = [d.id, d.country, d.age, d.work, d.money, d.mark, d.op_user, d.upload_time]
            sheet.append(row)
        book.save(filename)
    except BaseException:
        logging.info("create_excel fail")
        return None
    return filename


if __name__ == '__main__':
    data_list = [
        ExcelBean(
            no=0, id="123",
        ),
        ExcelBean(
            no=0, id="123",
        )
    ]
    create_excel(data_list, "D:\\")
