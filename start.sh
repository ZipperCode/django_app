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
echo "start sql success "
chmod 777 /tmp

dir="$(pwd)/data"
if [ ! -d "$dir" ];then
  mkdir "$dir"
  chmod 777 -R "$dir"
  echo "$dir 文件夹创建成功"
else
  chmod 777 -R "$dir"
  echo "$dir 文件夹已经存在"
fi

media_dir="$(pwd)/media"
if [ ! -d "$media_dir" ];then
  mkdir "$media_dir"
  chmod 777 -R "$media_dir"
  echo "$media_dir 文件夹创建成功"
else
  chmod 777 -R "$media_dir"
  echo "$media_dir 文件夹已经存在"
fi

echo "create data dir success"

java -version

python3 manage.py collectstatic --noinput
echo "exec migrate start======================================================================================"
python3 manage.py makemigrations
python3 manage.py migrate
echo "exec makemigrations web_app"
python3 manage.py makemigrations web_app
echo "exec migrate web_app"
python3 manage.py migrate web_app
#python3 manage.py migrate --fake web_app
echo "exec migrate end"

python3 manage.py collectstatic

uwsgi --ini /var/www/html/django_app/uwsgi.ini && tail -f /dev/null
exec "$@"
