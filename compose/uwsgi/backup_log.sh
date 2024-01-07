#!/bin/bash

backup_suffix=$1
echo "backup_suffix = $backup_suffix"
if [ -z "$backup_suffix" ]; then
    echo "backup_suffix not found"
    exit 1
fi
log_file_name="web_app-uwsgi.log"
if [ ! -f "${log_file_name}" ]; then
    echo "web_app-uwsgi.log not found"
    exit 1
fi

cp "$log_file_name" "backup_${backup_suffix}.log"

> $log_file_name

echo "success"
