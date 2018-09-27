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


bot = None
as_chat_robot = False
startForwarding = False
myself = u'Peter'
data_path = 'data'
ford_dict = {}
startTime = ''; endTime = '';
tz = pytz.timezone('Asia/Shanghai')#东八区时间

if __name__ == '__main__':
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    # if the QR code doesn't show correctly, you can try to change the value
    # of enableCdmQR to 1 or -1 or -2. It nothing works, you can change it to
    # enableCmdQR=True and a picture will show up.
    bot = itchat.new_instance()
    bot.auto_login(hotReload=True, enableCmdQR=2)
    nickname = bot.loginInfo['User']['NickName']
    print nickname, "login"

def get_whole_msg(msg, download=False):
    sending_type = {'Picture': 'img', 'Video': 'vid'}    
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
    elif '钱' in msg_send:
        msg_send = ''
    elif 'money' in msg_send:
        msg_send = ''
    else:
        msg_send = msg_send
    return msg_send

def show(publisher):
    print type(publisher)
    for key in publisher:
        print key,':',publisher[key]

def showFordDict(ford_dict):
    mymsg = 'ford_dict:\n'
    for key in ford_dict:
        mymsg += '\t' + str(key) + ' -> ' + str(ford_dict[key]) + '\n'
    return mymsg

@bot.msg_register([TEXT, NOTE, PICTURE, MAP, SHARING, ATTACHMENT, VIDEO, RECORDING],
        isFriendChat=True, isGroupChat=False)
def personal_msg(msg): #controller
    # print msg['Type']
    global as_chat_robot, startTime, endTime, ford_dict, myself, startForwarding

    publisher = bot.search_friends(userName=msg['FromUserName'])['NickName']
    if publisher == myself:
        text = msg['Text'].strip()
        if text == u"开始转发":
            print '进入开始转发模块'
            bot.send(u'准备启动自动转发功能', toUserName=msg['FromUserName'])
            bot.send(u'依次输入群1, 群2, startTime, endTime, 用逗号隔开:',toUserName=msg['FromUserName'])
            startForwarding = True
            return
        if text == "停止转发":
            print '进入停止转发模块'
            as_chat_robot = False
            startForwarding = False
            ford_dict={}
            startTime='';endTime=''
            bot.send(u'已停止自动转发',toUserName=msg['FromUserName'])
            return
        if text == "报告状态":
            now = datetime.datetime.fromtimestamp(int(time.time()), tz).strftime('%d-%H:%M')
            isIn = startTime < now < endTime
            mymsg = showFordDict(ford_dict)
            mymsg += 'startTime: {}, endTime: {}\nnow:{}, isIn:{}\nautoForwarding:{}'.format(startTime, endTime, now, isIn, as_chat_robot)
            bot.send(mymsg, toUserName=msg['FromUserName'])
            return
        
        if startForwarding: # 接受来自自己的命令
            params = msg['Text'].strip().split(',')
            if len(params) != 4:
                bot.send(u'输入格式错误，重新输入',toUserName=msg['FromUserName'])
                return
            else:
                publisher, receiver, startTime, endTime = [x.strip() for x in params]
                isPubExist = bot.search_chatrooms(name=publisher.decode('utf-8'))
                isRecExist = bot.search_chatrooms(name=receiver.decode('utf-8'))
                mymsg = u'找到群聊 ' + publisher + ' ' + str(len(isPubExist)) +u'个,'+ u'找到群聊 ' + receiver + ' '+ str(len(isRecExist)) +u'个'
                bot.send(mymsg,toUserName=msg['FromUserName'])

                if len(isPubExist)==1 and len(isRecExist)==1:
                    ford_dict[publisher.decode('utf-8')] = receiver.decode('utf-8')
                    ford_dict[receiver.decode('utf-8')] = publisher.decode('utf-8')
                    # ford_dict[isPubExist[0]['UserName']] = isRecExist[0]['UserName']
                    # ford_dict[isRecExist[0]['userName']] = isPubExist[0]['userName']
                    startForwarding = False
                    as_chat_robot = True
                    now = datetime.datetime.fromtimestamp(int(time.time()), tz).strftime('%d-%H:%M')
                    mymsg = 'start: ' + startTime + ' end: ' + endTime + ' now: ' + now + ' isIn: ' + str(startTime < now < endTime)
                    bot.send(mymsg, toUserName=msg['FromUserName'])
                    bot.send(u'启动成功',toUserName=msg['FromUserName'])
                    return
                elif len(isPubExist) + len(isRecExist) > 2:
                    bot.send(u'群聊命名重复',toUserName=msg['FromUserName'])
                else:
                    bot.send(u'未找到相应群聊',toUserName=msg['FromUserName'])
                    return

@bot.msg_register([TEXT, NOTE, PICTURE, MAP, SHARING, ATTACHMENT, VIDEO, RECORDING], isFriendChat=False, isGroupChat=True)
def group_msg(msg):
    global as_chat_robot, startTime, endTime, ford_dict, myself

    if as_chat_robot:
        publisher = bot.search_chatrooms(userName=msg['FromUserName'])['NickName'] #搜索消息发送者昵称
        if publisher not in ford_dict:
            print publisher, 'not in ford_dict'
            return
        now = datetime.datetime.fromtimestamp(int(time.time()), tz).strftime('%d-%H:%M')
        if startTime < now < endTime: # 在规定时间内进行转发
            print('MsgType:', msg['MsgType'])
            if msg['Type']=='Recording':
                bot.send(u"听不了语音，发文字吧",msg['FromUserName'])
            elif msg['MsgType'] == 49 and msg['AppMsgType'] == 2001:
                print('不转发红包消息')
            elif msg['MsgType'] == 10000 or msg['MsgType']==10002:
                print('不转系统消息')
                return
            elif msg['ActualNickName'] == myself:
                print('不转发自己消息')
                return
            else:
                # print(msg['ActualNickName'])
                receiver = bot.search_chatrooms(name=ford_dict[publisher])[0]['UserName']
                msg_send = get_whole_msg(msg, download=True) 
                msg_send = myfilter(msg_send)
                bot.send(msg_send, toUserName=receiver)
                return
        else:
            print now, 'Not in Fordwarding Time:', startTime,' to ', endTime
            return

if __name__ == '__main__':
    bot.run()
