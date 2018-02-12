# -*- coding: utf-8 -*-

import os
CWD=os.path.split(os.path.realpath(__file__))[0]

import re
from influxdb import InfluxDBClient
import configparser
import json
from libs.http_attachmail import http_send_attachmail
from libs.db import jsonDB
import logging
import shutil
import datetime
import uuid
import requests
from random import choice
import string


config = configparser.ConfigParser()
config.read(CWD+"/conf.ini")   # 注意这里必须是绝对路径

db_bind = jsonDB(CWD + "/db/bind.json")
db_who = jsonDB(CWD + "/db/who.json")

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

def sendMail(qq, cluster, app):
	imgdir = CWD + '/scripts/' + cluster + '_' + app
	imgname = imgdir + '/grafana.png'
	try:
		shutil.rmtree(imgdir)
	except:
		pass
	out = os.system(CWD+'/scripts/appStatus.sh ' + cluster + ' ' + app + ' &>>/tmp/renderImage.log')
	
	today,newname = cpImg(imgname)
	webfile = config.get('web', 'url') + '?date=' + today + "&id=" + newname
	
	addr = qq + '@qq.com'

	sub = '【监控图表】' + cluster + ':' + app
	filelist = [imgname]
	content = '<img style="max-width:100%;" class="aligncenter" src="cid:' + imgname + '" alt="app监控图表" />'
	
	#ret = http_send_attachmail(config.get('mail', 'api'), config.get('mail', 'server'), config.get('mail', 'user'), \
	#	config.get('mail', 'passwd'), addr, sub, content, filelist)
	ret = {'status':0,'msg':'邮件发送功能已停用'}
	addr = '(邮件发送功能已停用)'
	try:
		if ret['status'] != 0:
			errmsg = "邮件发送异常:" + ret['msg']
		else:
			errmsg = "【app状态查询】" + cluster + ":" + app + "\n邮件已发送至" + addr + ', 请查收\n在线查看:' + webfile
	except:
		errmsg = "邮件发送异常"
	
	return errmsg

def smilesRandom():
	smiles = config.get("msg", "smiles").split(",")
	return choice(smiles)

def cmdError(bot, contact):
	pre = config.get("msg", "pre").split(",")
	preChoice = choice(pre)
	help = config.get('msg', 'help')
	help = help.replace("提供以下指令",preChoice + smilesRandom())
	help = smilesRandom() + help + smilesRandom()
	help = help.replace("\\n", "\n")
	bot.SendTo(contact, help)
	
def appTrim(app):
	if re.match('^.*\.$', app):
		app = app.split(".")[0]
	elif re.match('^.*\.[0-9]{2,5}$', app):
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

def appStatus(content, cmd, qq):
	try:
		cluster = clusterTrim(cmd[1])
		app = appTrim(cmd[2])
		if not check("cluster", cluster) or not check("app", app):
			msg = "集群 " + cluster + "或APP " + app + "不存在"
			msg = msg + "\n" + config.get('msg', 'cluster') + "\n" + config.get('msg', 'app')
			msg = msg.replace('\\n' , '\n')
			return msg
		errmsg = sendMail(qq, cluster, app)
		return errmsg
	except:
		logging.exception("Exception Logged")
		errmsg = "【app状态查询】执行异常"
		return errmsg

def mpaasSuperAdmin():
	super = config.get("app", "superadmin")
	super = super.split(",")
	return super

def deployApp(content, cmd, qq):
	try:
		cluster = clusterTrim(cmd[1])
		app = cmd[2]
		owner = _appOwner(app)
		user = db_who.select(qq)
		if not user:
			user = "用户未绑定邮箱"
		if not owner or not check("cluster", cluster):
			msg = "集群 " + cluster + "或APP " + app + "不存在"
			msg = msg + "\n" + config.get('msg', 'cluster').replace('\\n', '\n')
			msg = msg + "\n" + "【APP】需要先录入CMDB才能使用机器人部署"
			return msg
		superadmin = mpaasSuperAdmin() + owner
		if user not in superadmin:
			msg = "【APP重部】" + user + " 没有权限操作 " + app
			return msg
		#return config.get("app", "mpaasupdate")
		msg = os.popen(config.get("app", "mpaasupdate") + " -cluster " + cluster + " -app " + app + \
			" -email " + user).read()
		if not msg:
			msg = "【APP重部】执行异常"
		return msg
	except:
		logging.exception("Exception Logged")
		errmsg = "【APP重部】执行异常"
		return errmsg
		
def diskClean(content, cmd):
	return("此功能暂不可用")

def _appOwner(app):
	api = config.get("cmdb", "pubapi")
	r = requests.get(api + "?type=app&value=" + app)
	d = r.json()
	c = d['objects']
	if not c:
		return([])
	owner = []
	for k,v in c.items():
		owner.append(v['fields']['friendlyname'] + '(' + v['fields']['phone'] + ')')
	return(owner)

def appOwner(content, cmd):
	try:
		app = cmd[1]
		owner = _appOwner(app)
		if not owner:
			return("【APP联系人查询】 未找到APP：" + app)
		owner = "\n           ".join(owner)
		link = config.get("cmdb", "linkapi") + "&type=app&name=" + app
		errmsg = "APP: " + app + "\n联系人: " + owner + "\nAPP关联图: " + link
		return errmsg
	except:
		logging.exception("Exception Logged")
		errmsg = "【app联系人查询】执行异常"
		return errmsg

def appFilter(app):
	if re.match('.*第三方代理.*', app):
		return False
	return True

def appMap(app):
	app = app.split('::')[2]
	app = re.sub('.*?\.(.*)', '\\1', app)
	return app	

def myCIs(contend, cmd):
	hide = "&hide=all"
	api = config.get("cmdb", "pubapi")
	try:
		person = cmd[1]
		r = requests.get(api + "?type=person&value=" + person + "&show=ApplicationSolution,Person&depth=1")
		d = r.json()
		relations = d['relations']
		apps = list(relations.keys())
		apps = filter(appFilter, apps)
		apps = map(appMap, apps)
		apps = ", ".join(apps)

		link = re.sub('\?.*', '', config.get("cmdb", "linkapi")) + "?type=person&name=" + person + hide
		return(person + "负责的APP: \n" + apps + "\n" + link)
	except:
		logging.exception("Exception Logged")
		errmsg = "【人员名下APP查询】执行异常"
		return errmsg
		
	
def isAdmin(qq):
	admins = config.get("qqbot", "admin").split(",")
	if db_who.select(qq) in admins:
		return True
	return False

def manageBot(bot, contact, content, qq):
	if not isAdmin(qq):
		return False
	if re.match('^-stop$', content):
		bot.SendTo(contact, smilesRandom() + "qqbot即将关闭")
		bot.Stop()
	elif re.match('^-fresh$', content):
		bot.SendTo(contact, smilesRandom() + "qqbot即将重启, 需要重新登录")
		bot.FreshRestart()
	elif re.match('^-restart$', content):
		bot.SendTo(contact, smilesRandom() + "qqbot即将重启")
		bot.Restart()
	
def customCmd(content, qq):
	if not isAdmin(qq):
		return False
	cmd = config.get("command", content)
	msg = os.popen(cmd).read()
	if not msg:
		msg = cmd + "执行异常"
	return str(msg)

def randpass(length=20, chars=string.ascii_letters+string.digits):
	return ''.join([choice(chars) for i in range(length)])

def bind(cmd, qq):
	count = len(cmd)
	user = cmd[1]
	if count == 2:
		password = randpass()
		db_bind.update(user,password)
		sub = "qqbot 绑定邮箱"
		content = "请向机器人发送以下指令完成绑定:   bind " + user + " " + password
		filelist = []
		try:
			ret = http_send_attachmail(config.get('mail', 'api'), config.get('mail', 'server'), \
				config.get('mail', 'user'), config.get('mail', 'passwd'), user, sub, content, filelist)
			if ret['status'] != 0:
				return("邮件发送异常:" + ret['msg'])
			else:
				return("邮件已发送:" + user)
		except:
			return("邮件发送异常")
	if count == 3:
		if db_bind.select(user) == cmd[2]:
			db_who.update(qq,user)
			return("uin: " + qq + " 已绑定邮箱 " + user)
		else:
			return("绑定失败")

def who(qq):
	return("you are: " + db_who.select(qq))

def showHelp(contend, cmd):
	options = config.options('msg')
	h = []
	for item in options:
		h.append("help " + item)
	h.remove("help help")

	try:
		return(config.get("msg", cmd[1]).replace("\\n", "\n"))
	except:
		return(config.get("msg", "help").replace("\\n", "\n") + "\n\n使用以下指令查看更多帮助:\n" + "\n".join(h))

def onQQMessage(bot, contact, member, content):
	if contact.ctype == "group" and ('@ME' not in content):
		return False
	
	content = content.replace('[@ME]  ', '')
	cmd = content.split(' ')
	contentTrim = content.replace('#', '')
	
	# 获取消息发送者QQ号(目前无法获取到qq号，使用UIN代替)
	# bot.SendTo(contact,json.dumps(contact.__dict__))
	if contact.ctype == "group":
		qq = member.uin
	else:
		qq = contact.uin
	
	if re.match('^st\s.*', content):
		bot.SendTo(contact, smilesRandom() + appStatus(content, cmd, qq))
	elif re.match('^dp\s.*', content):
		bot.SendTo(contact, smilesRandom() + deployApp(content, cmd, qq))
	elif re.match('^c\s.*', content):
		bot.SendTo(contact, smilesRandom() + diskClean(content, cmd))
	elif re.match('^o\s.*', content):
		bot.SendTo(contact, smilesRandom() + appOwner(content, cmd))
	elif re.match('^u\s.*', content):
		bot.SendTo(contact, smilesRandom() + myCIs(content, cmd))
	elif re.match('^who$', content):
		bot.SendTo(contact, smilesRandom() + who(qq))
	elif re.match('^bind\s.*', content):
		bot.SendTo(contact, smilesRandom() + bind(cmd,qq))
	elif re.match('^-.*', content):
		manageBot(bot, contact, content,qq )
	elif contentTrim in config.options("command"):
		bot.SendTo(contact, smilesRandom() + customCmd(contentTrim, qq))
	else:
		cmdError(bot, contact)

if __name__ == '__main__':
	print(check("newtv", "accounssts"))
