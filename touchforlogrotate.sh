#!/bin/bash

DIR=`echo $(cd "$(dirname "$0")"; pwd)`

echo "uwsgi log cut dir = $DIR"
LOGDIR="${DIR}/compose/uwsgi/logs"

if [ ! -d "$LOGDIR" ];then
  echo "$LOGDIR 不存在，创建目录"
  mkdir "$LOGDIR"
  chmod 777 -R "$LOGDIR"
fi

sourcelogpath="${DIR}/compose/uwsgi/web_tg-uwsgi.log"
touchfile="${DIR}/compose/uwsgi/.touchforlogrotate"

DATE=`date -d "yesterday" +"%Y-%m-%d"`
echo $DATE
destlogpath="${LOGDIR}/web_tg-uwsgi-${DATE}.log"

echo "$touchfile touchfile文件"
echo "$sourcelogpath 源文件目录"
echo "$destlogpath 目标文件"

mv $sourcelogpath $destlogpath
touch "$touchfile"
