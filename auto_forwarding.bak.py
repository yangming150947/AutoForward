# coding:utf-8

import sys
reload(sys)
sys.setdefaultencoding('UTF-8')

import os, re, shutil, time, collections, json
import datetime, pytz, time
from HTMLParser import HTMLParser
from xml.etree import ElementTree as ETree
import itchat
from itchat.content import *


if len(sys.argv) < 5:
    print('args: User1, User2, fromTime, toTime')

user1 = sys.argv[1].decode('utf-8')
user2 = sys.argv[2].decode('utf-8')
startTime = sys.argv[3].decode('utf-8')
endTime = sys.argv[4].decode('utf-8')

print 'user1:',user1, 'user2:',user2, 'startTime:',startTime, 'endTime:', endTime

tz = pytz.timezone('Asia/Shanghai')#东八区时间
sending_type = {'Picture': 'img', 'Video': 'vid'}
data_path = 'data'
ford_dict = {user1:user2, user2:user1}

bot = None


if __name__ == '__main__':
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    # if the QR code doesn't show correctly, you can try to change the value
    # of enableCdmQR to 1 or -1 or -2. It nothing works, you can change it to
    # enableCmdQR=True and a picture will show up.
    bot = itchat.new_instance()
    bot.auto_login(hotReload=True, enableCmdQR=2)
    nickname = bot.loginInfo['User']['NickName']
    print nickname


def get_whole_msg(msg, download=False):
    if len(msg['FileName']) > 0 and len(msg['Url']) == 0:
        if download: # download the file into data_path directory
            fn = os.path.join(data_path, msg['FileName'])
            msg['Text'](fn)
            if os.path.getsize(fn) == 0:
                return []
            c = '@%s@%s' % (sending_type.get(msg['Type'], 'fil'), fn) # 在sending_type中的key将被取出value，否则返回fil类型
        else:
            c = '@%s@%s' % (sending_type.get(msg['Type'], 'fil'), msg['FileName'])
        return c
    c = msg['Text']
    if len(msg['Url']) > 0:
        if len(msg['OriContent']) > 0:
            try: # handle map label
                content_tree = ETree.fromstring(msg['OriContent'])
                if content_tree is not None:
                    map_label = content_tree.find('location')
                    if map_label is not None:
                        c += ' ' + map_label.attrib['poiname']
                        c += ' ' + map_label.attrib['label']
            except:
                pass
        url = HTMLParser().unescape(msg['Url'])
        c += ' ' + url
    return c

def myfilter(msg_send): #实现消息过滤
    if '老板' in msg_send:
        msg_send = '在吗？'
    elif '微信' in msg_send:
        msg_send = ''
    elif 'wechat' in msg_send:
        msg_send = ''
    elif 'wexin' in msg_send:
        msg_send = ''
    else:
        msg_send = msg_send
    return msg_send


@bot.msg_register([TEXT, NOTE, PICTURE, MAP, SHARING, ATTACHMENT, VIDEO, RECORDING],
        isFriendChat=True, isGroupChat=False)
def personal_msg(msg):
    print msg['Type']
    now = datetime.datetime.fromtimestamp(int(time.time()), tz).strftime('%d-%H:%M')
    if startTime < now < endTime: # 在规定时间内进行转发
    
        publisher = bot.search_friends(userName=msg['FromUserName'])['NickName'] #搜索消息发送者昵称
        if publisher not in ford_dict: #不在转发列表中不转发
            print 'Not in ford dict:', publisher
            return
        elif msg['Type']=='Recording':
            bot.send(u"听不了语音，发文字吧",msg['FromUserName'])
        else:
            receiver = bot.search_friends(nickName=ford_dict[publisher])[0]['UserName']
            print 'receiver:',ford_dict[publisher],'id:',receiver
            msg_send = get_whole_msg(msg, download=True) 
            msg_send = myfilter(msg_send)
            bot.send(msg_send, toUserName=receiver)
    else:
        print now, 'Not in Fordwarding Time:', startTime,' to ', endTime
    # bot.send("hello world", toUserName=receiver)

if __name__ == '__main__':
    bot.run()


