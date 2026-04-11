#!/bin/bash
# 将 AccountLink2 的数据迁移到 AccountLink1 中
# 冲突规则：link 字段已存在则跳过
# 冲突数据导出为 CSV，合并完成后清空 AccountLink2 表

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "开始迁移 AccountLink2 -> AccountLink1 ..."

# 通过 docker exec 在 web 容器中执行
docker exec -i django_app-web-1 python manage.py shell << 'PYTHON_SCRIPT'
import csv
import os
from web_app.model.link import AccountLink, AccountLink2

csv_path = os.path.join(os.getcwd(), "merge_link2_to_link1.csv")

# 获取 AccountLink1 中已有的 link 集合
existing_links = set(AccountLink.objects.values_list("link", flat=True))

# 获取 AccountLink2 中所有数据
link2_items = list(AccountLink2.objects.all())

conflict_rows = []
migrate_count = 0
conflict_count = 0

for item in link2_items:
    if item.link in existing_links:
        # 冲突：跳过并记录
        conflict_rows.append({
            "id": item.id,
            "link": item.link,
            "remark": item.remark or "",
            "op_user_id": item.op_user_id or "",
            "used": item.used,
            "create_time": item.create_time or "",
            "update_time": item.update_time or "",
        })
        conflict_count += 1
    else:
        # 不冲突：迁移到 AccountLink1
        AccountLink.objects.create(
            link=item.link,
            remark=item.remark,
            op_user_id=item.op_user_id,
            used=item.used,
            create_time=item.create_time,
            update_time=item.update_time,
        )
        existing_links.add(item.link)
        migrate_count += 1

# 导出冲突数据到 CSV
if conflict_rows:
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "link", "remark", "op_user_id", "used", "create_time", "update_time"
        ])
        writer.writeheader()
        writer.writerows(conflict_rows)
    print(f"冲突数据已导出到: {csv_path}")
else:
    print("无冲突数据，未生成 CSV 文件。")

print(f"迁移完成: 成功 {migrate_count} 条, 冲突跳过 {conflict_count} 条。")

# 清空 AccountLink2 表
if link2_items:
    AccountLink2.objects.all().delete()
    print("AccountLink2 表数据已清空。")
else:
    print("AccountLink2 表为空，无需清空。")
PYTHON_SCRIPT

echo "迁移脚本执行完毕～"
