#!/bin/sh
#-u 后面改为自己的数据库账号
#-p 后面改为自己的数据库密码,有字符需要加""
#demand_database改为你想要备份的数据库名称
echo "开始备份数据库";
# 导出所有数据库 username 替换为自己mysql登陆名，password123登陆密码**
## mysqldump -h106.14.XX.XXX -uusername -p"password123" --all-databases > /data/mysqlbackup/databaseName`date +%Y-%m-%d_%H%M%S`.sql;

# 导出指定数据库并压缩
## mysqldump -h106.14.XX.XXX -uusername -p"password123"  demand_database| gzip > /data/mysqlbackup/databaseName`date +%Y-%m-%d_%H%M%S`.sql.gz;

# 最近转投docker怀抱，本地不安装mysql时，采用docker的mysql备份，备份语句修改为**
docker exec mysql sh -c 'exec mysqldump --all-databases -utemegram -p949389 --all-databases' > /data/backup/database_`date +%Y-%m-%d_%H%M%S`.sql;

# mysql 替换为对应的容器名
# 删除 3 天前的备份文件

backupdir=/data/backup
db_name=databaseName_

find $backupdir -name $db_name"*.sql.gz" -type f -mtime +3 -exec rm -rf {} \;


echo "备份完成";
