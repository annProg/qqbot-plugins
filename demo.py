# -*- coding: utf-8 -*-

import re
import configparser
config = configparser.ConfigParser()
config.read("conf.ini")   # 注意这里必须是绝对路径

st = config.get('msg', 'help')
st = st.replace('#', "\n")
print(st)

def onQQMessage(bot, contact, member, content):
    if content == 'hel':
        bot.SendTo(contact, "你好，我是\nQQ机器人")
