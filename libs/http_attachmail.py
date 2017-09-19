#!/usr/bin/env python3
#-*- coding:utf-8 -*-  

############################
# Usage:
# File Name: sms.py
# Author: annhe  
# Mail: i@annhe.net
# Created Time: 2016-07-05 14:59:40
############################

from requests_toolbelt import MultipartEncoder
import requests
import json
import time
import sys

log="/tmp/http_mail.log"

def sendlog(status, to_list, subject):
	curdate = time.strftime('%F %X')
	with open(log, 'a+') as f:
		f.write(curdate + " " + status + " " + to_list + " " + subject + "\n")

def http_send_attachmail(mail_api, server, user, passwd, to, sub, content, filelist=[], mail_format="html", mail_from=""):
	attachNum = str(len(filelist))
	attachs = {}
	i = 1
	for attach in filelist:
		idx = 'attach' + str(i)
		attachs[idx] = (attach, open(attach, "rb"))
		i+=1
	mailFrom = {}
	if mail_from != "":
		mailFrom['from'] = mail_from
	fields = {"server":server, "user":user, "passwd":passwd, "tos":to, \
		"subject":sub, "content":content, "format":mail_format, "attachNum":attachNum}
	fields = dict(fields, **attachs)
	fields = dict(fields, **mailFrom)
	m = MultipartEncoder(fields)
	headers = {"content-type":m.content_type}
	r = requests.post(mail_api, data=m, headers=headers)
	ret = r.json()
	status = str(ret['status']) + "-" + ret['msg']
	sendlog(status, to, sub)
	return ret

if __name__ == '__main__':
	to=sys.argv[1]
	msg="http_mail测试<img src=\"cid:/root/file1.png\"/>"
	mail_api = "http://localhost:3001/api/attachmail"
	server = sys.argv[2]
	user = sys.argv[3]
	passwd = sys.argv[4]
	ret = http_send_attachmail(mail_api, server, user, passwd, to,"http_mail测试", msg, ["/root/file1.png"])
	print(ret)

