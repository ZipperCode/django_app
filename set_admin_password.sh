#!/bin/bash
# 设置 admin 用户的密码为 zipper949389

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "正在设置 admin 用户密码 ..."

python manage.py shell << 'PYTHON_SCRIPT'
from web_app.model.users import User

username = "admin"
new_password = "zipper949389"

user = User.objects.filter(username=username).first()
if user is None:
    print(f"错误: 用户 '{username}' 不存在！")
    exit(1)

user.password = new_password
user.save(update_fields=["password"])
print(f"成功: 用户 '{username}' 的密码已设置为 '{new_password}'")
PYTHON_SCRIPT

echo "操作完成喵～"
