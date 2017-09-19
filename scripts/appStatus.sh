#!/bin/bash

############################
# Usage:
# File Name: grafana_image.sh
# Author: annhe  
# Mail: i@annhe.net
# Created Time: 2017-09-14 18:19:50
############################

[ $# -lt 2 ] && echo "$0 cluster app" && exit 1

CWD=`cd $(dirname $0);pwd`
cd $CWD

# 请在conf.sh中定义以下变量
GRAFANA="http://grafana.xxx.com"
KEY="eyJrRQZkVjM3J1bjRqNGliNGhWV1IiLCJuIjoicG5nIiwiaWQiOjF9"
CLUSTER=$1
APP=$2
MPAAS_APP=`echo $APP |sed -r 's/\..*?//g'`

source ./conf.sh

TrimCluster=`echo $CLUSTER |tr -d '-'`
eval ROUTER="\$$TrimCluster"
[ "$ROUTER"x = ""x ] && ROUTER="All"

NOW=`date +%s`
START=`echo $NOW|awk '{print $1-1800}'`
NOW="${NOW}000"
START="${START}000"
WIDTH="600"
HEIGHT="150"
COMMON="render/dashboard-solo/db/ying-yong-zhuang-tai-jian-kong?refresh=30s&orgId=1&var-cluster=$CLUSTER&var-router=All&var-app=$APP&var-mpaas_app=$MPAAS_APP&from=$START&to=$NOW&width=$WIDTH&height=$HEIGHT&tz=UTC%2B08%3A00&panelId="

IMGDIR="${CLUSTER}_${APP}"
[ ! -d $IMGDIR ] && mkdir $IMGDIR

cd $IMGDIR
for id in ${panelId[@]};do
	curl -s -H "Authorization: Bearer $KEY" "$GRAFANA/$COMMON$id" -o "${CLUSTER}_${APP}_${id}.png"
done

convert *.png -append grafana.png
