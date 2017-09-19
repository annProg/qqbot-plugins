# -*- coding: utf-8 -*-

import os
CWD=os.path.split(os.path.realpath(__file__))[0]

import re
from influxdb import InfluxDBClient
import configparser
import json
from libs.http_attachmail import http_send_attachmail
import logging
import shutil
import datetime
import uuid
import requests


config = configparser.ConfigParser()
config.read(CWD+"/conf.ini")   # 注意这里必须是绝对路径

logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
        datefmt='%a, %d %b %Y %H:%M:%S',
        filename=config.get('log', 'err'))

influx = InfluxDBClient(config.get("influxdb", "server"),
	config.get("influxdb", "port"),
	config.get("influxdb", "user"),
	config.get("influxdb", "passwd"),
	config.get("influxdb", "database"))

def check(type, value):
	r = influx.query('show tag values from "reqstat" with key="' + type + '"')
	for i in list(r.get_points()):
		if i['value'] == value:
			return True
	return False
def cpImg(imgname):
	today = str(datetime.date.today())
	webdir = config.get('web', 'dir')
	destdir = webdir + '/' + today
	if not os.path.exists(destdir):
		os.mkdir(destdir)
	newname = str(uuid.uuid1()) + '.png'
	shutil.copy(imgname, destdir + '/' + newname)
	return today,newname

def sendMail(contact, cluster, app, member):
	imgdir = CWD + '/scripts/' + cluster + '_' + app
	imgname = imgdir + '/grafana.png'
	try:
		shutil.rmtree(imgdir)
	except:
		pass
	out = os.system(CWD+'/scripts/appStatus.sh ' + cluster + ' ' + app + ' &>>/tmp/renderImage.log')
	
	today,newname = cpImg(imgname)
	webfile = config.get('web', 'url') + '?date=' + today + "&id=" + newname
	
	if contact.ctype == "group":
		addr = member.qq + '@qq.com'
	else:
		addr = contact.qq + '@qq.com'
	sub = '【监控图表】' + cluster + ':' + app
	filelist = [imgname]
	content = '<img style="max-width:100%;" class="aligncenter" src="cid:' + imgname + '" alt="app监控图表" />'
	
	ret = http_send_attachmail(config.get('mail', 'api'), config.get('mail', 'server'), config.get('mail', 'user'), \
		config.get('mail', 'passwd'), addr, sub, content, filelist)
	try:
		if ret['status'] != 0:
			errmsg = "邮件发送异常:" + ret['msg']
		else:
			errmsg = "【app状态查询】" + cluster + ":" + app + "\n邮件已发送至" + addr + ', 请查收\n在线查看:' + webfile
	except:
		errmsg = "邮件发送异常"
	
	return errmsg

def cmdError(bot, contact):
	help = config.get('msg', 'help')
	help = help.replace("\\n", "\n")
	bot.SendTo(contact, help)
	
def appTrim(app):
	if re.match('^.*\.$', app):
		app = app.split(".")[0]
	elif re.match('^.*\.[0-9]{2-5}$', app):
		app = app
	else:
		app = app + ".8080"
	return app

def clusterTrim(cluster):
	clusterMap = config.get("app", "cluster")
	clusterMap = clusterMap.split(",")
	cMap = {}
	for item in clusterMap:
		t = item.split("=")
		cMap[t[0]] = t[1]
	
	if cluster in cMap.keys():
		return cMap[cluster]
	else:
		return cluster

def appStatus(content,contact, member):
	cmd = content.split(' ')
	try:
		cluster = clusterTrim(cmd[1])
		app = appTrim(cmd[2])
		if not check("cluster", cluster) or not check("app", app):
			msg = "集群" + cluster + "或APP" + app + "不存在"
			msg = msg + "\n" + config.get('msg', 'cluster') + "\n" + config.get('msg', 'app')
			msg = msg.replace('\\n' , '\n')
			return msg
		errmsg = sendMail(contact, cluster, app, member)
		return errmsg
	except:
		logging.exception("Exception Logged")
		errmsg = "【app状态查询】执行异常"
		return errmsg

def deployApp(content):
	return("此功能暂不可用")

def diskClean(content):
	return("此功能暂不可用")

def appOwner(content):
	api = config.get("cmdb", "pubapi")
	cmd = content.split(' ')
	try:
		app = cmd[1]
		r = requests.get(api + "?type=app&value=" + app)
		d = r.json()
		c = d['objects']
		contact = []
		for k,v in c.items():
			contact.append(v['fields']['friendlyname'] + '(' + v['fields']['phone'] + ')')
		contact = "\n           ".join(contact)
		link = config.get("cmdb", "linkapi") + "&type=app&name=" + app
		errmsg = "APP: " + app + "\n联系人: " + contact + "\nAPP关联图: " + link
		return errmsg
	except:
		logging.exception("Exception Logged")
		errmsg = "【app联系人查询】执行异常"
		return errmsg

def onQQMessage(bot, contact, member, content):
	if contact.ctype == "group" and ('@ME' not in content):
		return False
	
	content = content.replace('[@ME]  ', '')
	if re.match('^st\s.*', content):
		bot.SendTo(contact, appStatus(content,contact, member))
	elif re.match('^dp\s.*', content):
		bot.SendTo(contact, deployApp(content))
	elif re.match('^c\s.*', content):
		bot.SendTo(contact, diskClean(content))
	elif re.match('^o\s.*', content):
		bot.SendTo(contact, appOwner(content))
	else:
		cmdError(bot, contact)

if __name__ == '__main__':
	print(check("newtv", "accounssts"))
