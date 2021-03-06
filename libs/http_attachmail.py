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

def http_send_attachmail(mail_api, to, sub, content, filelist=[], mail_format="html", mail_from=""):
	attachNum = str(len(filelist))
	attachs = {}
	i = 1
	for attach in filelist:
		idx = 'attach' + str(i)
		attachs[idx] = (attach, open(attach, "rb"))
		i+=1
	fields = {"tos":to, \
		"subject":sub, "content":content, "format":mail_format, "attachNum":attachNum}
	fields = dict(fields, **attachs)
	m = MultipartEncoder(fields)
	headers = {"content-type":m.content_type}
	r = requests.post(mail_api, data=m, headers=headers)
	try:
		ret = r.json()
		status = str(ret['status']) + "-" + ret['msg']
		return ret
	except:
		sendlog(r.text,to,sub)
		return {'status':10,'msg':r.text}

if __name__ == '__main__':
	to=sys.argv[1]
	msg="http_mail测试<img src=\"cid:/root/file1.png\"/>"
	mail_api = "http://localhost:3001/api/attachmail"
	ret = http_send_attachmail(mail_api, to,"http_mail测试", msg, ["/root/file1.png"])
	print(ret)

