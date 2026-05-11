#!/bin/bash
# 设置 admin 用户的密码为 black258369

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "正在设置 admin 用户密码 ..."

docker exec -i django_app-web-1 python manage.py shell << 'PYTHON_SCRIPT'
from hashlib import md5
from web_app.model.users import User

username = "admin"
new_password = "black258369"

user = User.objects.filter(username=username).first()
if user is None:
    print(f"错误: 用户 '{username}' 不存在！")
    exit(1)

# 使用项目已有的 MD5 加密方式
user.password = md5(new_password.encode()).digest().hex().lower()
user.save(update_fields=["password"])
print(f"成功: 用户 '{username}' 的密码已加密设置")
PYTHON_SCRIPT

echo "操作完成喵～"
