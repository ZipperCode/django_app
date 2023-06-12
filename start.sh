#!/bin/bash
# 从第一行到最后一行分别表示：
# 1. 等待MySQL服务启动后再进行数据迁移。nc即netcat缩写
# 2. 收集静态文件到根目录static文件夹，
# 3. 生成数据库可执行文件，
# 4. 根据数据库可执行文件来修改数据库
# 5. 用 uwsgi启动 django 服务
# 6. tail空命令防止web容器执行脚本后退出
while ! nc -z db 3306 ; do
    echo "Waiting for the MySQL Server"
    sleep 3
done

dir="$(pwd)/data"
if [ ! -d "$dir" ];then
  mkdir "$dir"
  chmod 777 -R "$dir"
  echo "$dir 文件夹创建成功"
else
  chmod 777 -R "$dir"
  echo "$dir 文件夹已经存在"
fi

python3 manage.py collectstatic --noinput
echo "exec migrate start======================================================================================"
python3 manage.py makemigrations&&
python3 manage.py migrate
echo "exec makemigrations web_tg"
python3 manage.py makemigrations web_app
echo "exec migrate web_tg"
python3 manage.py migrate web_app
echo "exec migrate end"
uwsgi --ini /var/www/html/web_tg_chat/uwsgi.ini&&
tail -f /dev/null

exec "$@"