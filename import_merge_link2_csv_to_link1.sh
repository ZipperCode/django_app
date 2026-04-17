#!/bin/bash
# 将 merge_link2_to_link1.csv 中导出的冲突数据直接导入到 AccountLink1 中
# 忽略 CSV 中的 id，保留 link/remark/op_user_id/used/create_time/update_time 原值

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

CSV_PATH="${1:-merge_link2_to_link1.csv}"

echo "开始导入 CSV 到 AccountLink1 ..."

# 通过 docker exec 在 web 容器中执行
docker exec -i -e IMPORT_CSV_PATH="$CSV_PATH" django_app-web-1 python manage.py shell << 'PYTHON_SCRIPT'
import csv
import os
from datetime import datetime

from django.db import connection, transaction
from django.utils.dateparse import parse_datetime

from web_app.model.const import UsedStatus
from web_app.model.link import AccountLink


def parse_int(value, *, default=None, row_num, field_name):
    value = (value or "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"第 {row_num} 行字段 {field_name} 不是合法整数: {value}") from exc


def parse_csv_datetime(value, *, row_num, field_name):
    value = (value or "").strip()
    if not value:
        return None

    parsed = parse_datetime(value)
    if parsed is not None:
        if parsed.tzinfo is not None:
            return parsed.replace(tzinfo=None)
        return parsed

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(f"第 {row_num} 行字段 {field_name} 不是合法时间: {value}")


csv_path = os.environ.get("IMPORT_CSV_PATH") or "merge_link2_to_link1.csv"
if not os.path.isabs(csv_path):
    csv_path = os.path.join(os.getcwd(), csv_path)

if not os.path.exists(csv_path):
    raise FileNotFoundError(f"未找到 CSV 文件: {csv_path}")

with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    fieldnames = set(reader.fieldnames or [])
    if "link" not in fieldnames:
        raise ValueError("CSV 缺少必要字段: link")

    rows = []
    for row_num, row in enumerate(reader, start=2):
        link = (row.get("link") or "").strip()
        if not link:
            raise ValueError(f"第 {row_num} 行字段 link 不能为空")

        rows.append((
            link,
            row.get("remark", ""),
            parse_int(row.get("op_user_id"), default=None, row_num=row_num, field_name="op_user_id"),
            parse_int(row.get("used"), default=UsedStatus.Default, row_num=row_num, field_name="used"),
            parse_csv_datetime(row.get("create_time"), row_num=row_num, field_name="create_time"),
            parse_csv_datetime(row.get("update_time"), row_num=row_num, field_name="update_time"),
        ))

if not rows:
    print(f"CSV 没有可导入的数据: {csv_path}")
else:
    table_name = connection.ops.quote_name(AccountLink._meta.db_table)
    sql = (
        f"INSERT INTO {table_name} "
        "(link, remark, op_user_id, used, create_time, update_time) "
        "VALUES (%s, %s, %s, %s, %s, %s)"
    )

    with transaction.atomic():
        with connection.cursor() as cursor:
            batch_size = 1000
            for start in range(0, len(rows), batch_size):
                cursor.executemany(sql, rows[start:start + batch_size])

    print(f"导入完成: 成功插入 {len(rows)} 条记录。")
    print(f"CSV 文件: {csv_path}")

PYTHON_SCRIPT

echo "CSV 导入脚本执行完毕～"
