#!/bin/bash

# 设置日志文件路径
LOG_FILE="./compose/uswgi/web_app-uwsgi.log"

# 设置备份目录
BACKUP_DIR="./compose/uswgi/backup"

# 检查备份目录是否存在，不存在则创建
if [ ! -d "$BACKUP_DIR" ]; then
  mkdir -p "$BACKUP_DIR"
fi

# 获取当前日期时间，作为备份文件名的一部分
CURRENT_TIME=$(date +"%Y%m%d_%H%M%S")

# 创建备份文件路径
BACKUP_FILE="$BACKUP_DIR/logfile_$CURRENT_TIME.log"

# 备份日志文件
cp "$LOG_FILE" "$BACKUP_FILE"

# 清空原始日志文件
> "$LOG_FILE"

# 输出提示信息
echo "日志文件已备份至: $BACKUP_FILE"
echo "原日志文件已清空."
