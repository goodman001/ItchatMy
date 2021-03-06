import os, time, re, io
import base64
import threading
import json, xml.dom.minidom
import random
import traceback, logging

try:
    from httplib import BadStatusLine
except ImportError:
    from http.client import BadStatusLine

import requests
from pyqrcode import QRCode

from .. import config, utils
from ..utils import test_connect
from ..returnvalues import ReturnValue
from ..storage.templates import wrap_user_dict
from .contact import update_local_chatrooms, update_local_friends
from .messages import produce_msg
from PIL import Image as pilimgtools, ImageTk
logger = logging.getLogger('itchat')

def load_login(core):
    core.login             = login
    core.get_QRuuid        = get_QRuuid
    core.get_QR            = get_QR
    core.check_login       = check_login
    core.check_login_new   = check_login_new
    core.web_init          = web_init
    core.show_mobile_login = show_mobile_login
    core.start_receiving   = start_receiving
    core.get_msg           = get_msg
    core.logout            = logout
    core.new_login         = new_login
    core.getself_head_img  = getself_head_img

def login(self, enableCmdQR=False, picDir=None, qrCallback=None,
        loginCallback=None, exitCallback=None):
    if self.alive or self.isLogging:
        logger.warning('itchat has already logged in.')
        return
    self.isLogging = True
    while self.isLogging:
        uuid = push_login(self)
        if uuid:
            qrStorage = io.BytesIO()
        else:
            logger.info('Getting uuid of QR code.')
            while not self.get_QRuuid():
                time.sleep(1)
            logger.info('Downloading QR code.')
            qrStorage = self.get_QR(enableCmdQR=enableCmdQR,
                picDir=picDir, qrCallback=qrCallback)
            logger.info('Please scan the QR code to log in.')
        isLoggedIn = False
        while not isLoggedIn:
            status = self.check_login()
            if hasattr(qrCallback, '__call__'):
                qrCallback(uuid=self.uuid, status=status, qrcode=qrStorage.getvalue())
            if status == '200':
                isLoggedIn = True
            elif status == '201':
                if isLoggedIn is not None:
                    logger.info('Please press confirm on your phone.')
                    isLoggedIn = None
            elif status != '408':
                break
        if isLoggedIn:
            break
        elif self.isLogging:
            logger.info('Log in time out, reloading QR code.')
    else:
        return # log in process is stopped by user
    logger.info('Loading the contact, this may take a little while.')
    userinfo = self.web_init()
    print(userinfo)
    self.show_mobile_login()
    self.get_contact(True)
    if hasattr(loginCallback, '__call__'):
        r = loginCallback()
    else:
        utils.clear_screen()
        if os.path.exists(picDir or config.DEFAULT_QR):
            os.remove(picDir or config.DEFAULT_QR)
        print('Login successfully as %s' % self.storageClass.nickName)
    if self.downloadselfheadimg:
        print('#download self head image! ')
        try:
            temp=self.getself_head_img(userinfo['User']["HeadImgUrl"],userinfo['User']["UserName"])
            im = pilimgtools.open(io.BytesIO(temp))
            im.save(os.path.join('dist',userinfo['User']["UserName"]),'png')
        except Exception:
            print(u'加载自己的头像失败： ')
    else:
        print('#self head image has download ! ')
        im = pilimgtools.open(os.path.join('dist','self'))
        im.save(os.path.join('dist',userinfo['User']['UserName']),'png')
    print('#init main ui data ! ')
    signal_p([userinfo,contractslist,chatrooms],3)
    self.start_receiving(exitCallback,signal_m)
    self.isLogging = False
def new_login(self, signal_p,signal_m,hotReload=False, enableCmdQR=False, picDir=None, qrCallback=None,loginCallback=None, exitCallback=None):
    if not test_connect():
        logger.info("You can't get access to internet or wechat domain, so exit.")
        sys.exit()
    if self.alive or self.isLogging:
        logger.warning('itchat has already logged in.')
        sys.exit()
    def open_QR():
        for get_count in range(10):
            logger.info('get QR-UUID')
            while not self.get_QRuuid(): time.sleep(1)
            logger.info('generate QR-Code Image')
            if self.get_QR(): break
            elif get_count >= 9:
                logger.info('Failed to get QR Code, please restart the program')
                sys.exit()
        print('Please scan the QR Code')
    open_QR()
    self.downloadselfheadimg=True
    print("check login");
    while 1:
        status = self.check_login_new(signal_=signal_p)
        if status == '200':
            signal_p([config.updatedata],2)
            break
        elif status == '201':
            signal_p([config.pleaselogin],2)
            logger.info('content QR Code')
        elif status == '408':
            print('Reloading QR Code\n')
            signal_p([config.qrreset],2)
            open_QR()
            signal_p([config.DEFAULT_QR,config.QR_width,config.QR_height],1)
    logger.info("########################### init login info #############################")
    self.web_init()
    self.show_mobile_login()
    contractslist = self.get_contact(True)
    print('#get chatrooms data! ')
    chatrooms=self.get_chatrooms()
    if hasattr(loginCallback, '__call__'):
        r = loginCallback()
    else:
        utils.clear_screen()
        if os.path.exists(picDir or config.DEFAULT_QR):
            os.remove(picDir or config.DEFAULT_QR)
        print('Login successfully as %s' % self.storageClass.nickName)
    userinfo = self.web_init()
    print(userinfo)
    self.show_mobile_login()
    self.get_contact(True)
    if hasattr(loginCallback, '__call__'):
        r = loginCallback()
    else:
        utils.clear_screen()
        if os.path.exists(picDir or config.DEFAULT_QR):
            os.remove(picDir or config.DEFAULT_QR)
        print('Login successfully as %s' % self.storageClass.nickName)
    if self.downloadselfheadimg:
        print('#download self head image! ')
        try:
            temp=self.getself_head_img(userinfo['User']["HeadImgUrl"],userinfo['User']["UserName"])
            im = pilimgtools.open(io.BytesIO(temp))
            im.save(os.path.join('dist',userinfo['User']["UserName"]),'png')
        except Exception:
            print(u'加载自己的头像失败： ')
    else:
        print('#self head image has download ! ')
        im = pilimgtools.open(os.path.join('dist','self'))
        im.save(os.path.join('dist',userinfo['User']['UserName']),'png')
    print('#init main ui data ! ')
    signal_p([userinfo,contractslist,chatrooms],3)
    self.start_receiving(exitCallback,signal_m)
    self.isLogging = False
def getself_head_img(self,headurl,username=None):
    params = {
        'userName': username or self.storageClass.userName,
        'skey': self.loginInfo['skey'],
        }
    # 'type': 'big',
    url = 'https://wx2.qq.com'+headurl
    headers = { 'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36' }
    r = self.s.get(url, params=params, stream=True, headers=headers)
    tempStorage = io.BytesIO()
    for block in r.iter_content(1024):
        tempStorage.write(block)
    return tempStorage.getvalue()
def push_login(core):
    cookiesDict = core.s.cookies.get_dict()
    if 'wxuin' in cookiesDict:
        url = '%s/cgi-bin/mmwebwx-bin/webwxpushloginurl?uin=%s' % (
            config.BASE_URL, cookiesDict['wxuin'])
        headers = { 'User-Agent' : config.USER_AGENT }
        r = core.s.get(url, headers=headers).json()
        if 'uuid' in r and r.get('ret') in (0, '0'):
            core.uuid = r['uuid']
            return r['uuid']
    return False

def get_QRuuid(self):
    url = '%s/jslogin' % config.BASE_URL
    params = {
        'appid' : 'wx782c26e4c19acffb',
        'fun'   : 'new', }
    headers = { 'User-Agent' : config.USER_AGENT }
    r = self.s.get(url, params=params, headers=headers)
    regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)";'
    data = re.search(regx, r.text)
    if data and data.group(1) == '200':
        self.uuid = data.group(2)
        return self.uuid

def get_QR(self, uuid=None, enableCmdQR=True, picDir=None, qrCallback=None):
    uuid = uuid or self.uuid
    picDir = picDir or config.DEFAULT_QR
    qrStorage = io.BytesIO()
    qrCode = QRCode('https://login.weixin.qq.com/l/' + uuid)
    qrCode.png(qrStorage, scale=10)
    if hasattr(qrCallback, '__call__'):
        qrCallback(uuid=uuid, status='0', qrcode=qrStorage.getvalue())
    else:
        with open(picDir, 'wb') as f:
            f.write(qrStorage.getvalue())
        if enableCmdQR:
            utils.print_cmd_qr(qrCode.text(1), enableCmdQR=enableCmdQR)
        else:
            utils.print_qr(picDir)
    return qrStorage

def check_login(self, uuid=None):
    uuid = uuid or self.uuid
    url = '%s/cgi-bin/mmwebwx-bin/login' % config.BASE_URL
    localTime = int(time.time())
    params = 'loginicon=true&uuid=%s&tip=1&r=%s&_=%s' % (
        uuid, int(-localTime / 1579), localTime)
    headers = { 'User-Agent' : config.USER_AGENT }
    r = self.s.get(url, params=params, headers=headers)
    regx = r'window.code=(\d+)'
    data = re.search(regx, r.text)
    if data and data.group(1) == '200':
        if process_login_info(self, r.text):
            return '200'
        else:
            return '400'
    elif data:
        return data.group(1)
    else:
        return '400'
def check_login_new(self, uuid=None,signal_ = None):
    uuid = uuid or self.uuid
    url = '%s/cgi-bin/mmwebwx-bin/login' % config.BASE_URL
    localTime = int(time.time())
    params = 'loginicon=true&uuid=%s&tip=1&r=%s&_=%s' % (
        uuid, int(-localTime / 1579), localTime)
    headers = { 'User-Agent' : config.USER_AGENT }
    r = self.s.get(url, params=params, headers=headers)
    regx = r'window.code=(\d+)'
    data = re.search(regx, r.text)
    if data and data.group(1) == '200':
        if process_login_info(self, r.text):
            os.remove(config.DEFAULT_QR)
            return '200'
        else:
            return '400'
    elif data and data.group(1) == '201':
        if self.downloadselfheadimg:
            str_img=r.text.replace('window.code=201;window.userAvatar = \'data:img/jpg;base64,','').replace('\';','')
            with open(os.path.join('dist','self'), 'wb') as f:f.write(base64.b64decode(str_img)  )
            self.downloadselfheadimg=False
            signal_([],4)
            signal_([config.Self_Image_Path,config.Self_Image_Width,config.Self_Image_Height],1)
        return '201'
    elif data and data.group(1) == '408':
        return '408'
    else:
        return '400'
def process_login_info(core, loginContent):
    ''' when finish login (scanning qrcode)
     * syncUrl and fileUploadingUrl will be fetched
     * deviceid and msgid will be generated
     * skey, wxsid, wxuin, pass_ticket will be fetched
    '''
    regx = r'window.redirect_uri="(\S+)";'
    core.loginInfo['url'] = re.search(regx, loginContent).group(1)
    headers = { 'User-Agent' : config.USER_AGENT }
    r = core.s.get(core.loginInfo['url'], headers=headers, allow_redirects=False)
    core.loginInfo['url'] = core.loginInfo['url'][:core.loginInfo['url'].rfind('/')]
    for indexUrl, detailedUrl in (
            ("wx2.qq.com"      , ("file.wx2.qq.com", "webpush.wx2.qq.com")),
            ("wx8.qq.com"      , ("file.wx8.qq.com", "webpush.wx8.qq.com")),
            ("qq.com"          , ("file.wx.qq.com", "webpush.wx.qq.com")),
            ("web2.wechat.com" , ("file.web2.wechat.com", "webpush.web2.wechat.com")),
            ("wechat.com"      , ("file.web.wechat.com", "webpush.web.wechat.com"))):
        fileUrl, syncUrl = ['https://%s/cgi-bin/mmwebwx-bin' % url for url in detailedUrl]
        if indexUrl in core.loginInfo['url']:
            core.loginInfo['fileUrl'], core.loginInfo['syncUrl'] = \
                fileUrl, syncUrl
            break
    else:
        core.loginInfo['fileUrl'] = core.loginInfo['syncUrl'] = core.loginInfo['url']
    core.loginInfo['deviceid'] = 'e' + repr(random.random())[2:17]
    core.loginInfo['logintime'] = int(time.time() * 1e3)
    core.loginInfo['BaseRequest'] = {}
    for node in xml.dom.minidom.parseString(r.text).documentElement.childNodes:
        if node.nodeName == 'skey':
            core.loginInfo['skey'] = core.loginInfo['BaseRequest']['Skey'] = node.childNodes[0].data
        elif node.nodeName == 'wxsid':
            core.loginInfo['wxsid'] = core.loginInfo['BaseRequest']['Sid'] = node.childNodes[0].data
        elif node.nodeName == 'wxuin':
            core.loginInfo['wxuin'] = core.loginInfo['BaseRequest']['Uin'] = node.childNodes[0].data
        elif node.nodeName == 'pass_ticket':
            core.loginInfo['pass_ticket'] = core.loginInfo['BaseRequest']['DeviceID'] = node.childNodes[0].data
    if not all([key in core.loginInfo for key in ('skey', 'wxsid', 'wxuin', 'pass_ticket')]):
        logger.error('Your wechat account may be LIMITED to log in WEB wechat, error info:\n%s' % r.text)
        core.isLogging = False
        return False
    return True

def web_init(self):
    url = '%s/webwxinit' % self.loginInfo['url']
    params = {
        'r': int(-time.time() / 1579),
        'pass_ticket': self.loginInfo['pass_ticket'], }
    data = { 'BaseRequest': self.loginInfo['BaseRequest'], }
    headers = {
        'ContentType': 'application/json; charset=UTF-8',
        'User-Agent' : config.USER_AGENT, }
    r = self.s.post(url, params=params, data=json.dumps(data), headers=headers)
    dic = json.loads(r.content.decode('utf-8', 'replace'))
    # deal with login info
    utils.emoji_formatter(dic['User'], 'NickName')
    self.loginInfo['InviteStartCount'] = int(dic['InviteStartCount'])
    self.loginInfo['User'] = wrap_user_dict(utils.struct_friend_info(dic['User']))
    self.memberList.append(self.loginInfo['User'])
    self.loginInfo['SyncKey'] = dic['SyncKey']
    self.loginInfo['synckey'] = '|'.join(['%s_%s' % (item['Key'], item['Val'])
        for item in dic['SyncKey']['List']])
    self.storageClass.userName = dic['User']['UserName']
    self.storageClass.nickName = dic['User']['NickName']
    # deal with contact list returned when init
    contactList = dic.get('ContactList', [])
    chatroomList, otherList = [], []
    for m in contactList:
        if m['Sex'] != 0:
            otherList.append(m)
        elif '@@' in m['UserName']:
            m['MemberList'] = [] # don't let dirty info pollute the list
            chatroomList.append(m)
        elif '@' in m['UserName']:
            # mp will be dealt in update_local_friends as well
            otherList.append(m)
    if chatroomList:
        update_local_chatrooms(self, chatroomList)
    if otherList:
        update_local_friends(self, otherList)
    return dic

def show_mobile_login(self):
    url = '%s/webwxstatusnotify?lang=zh_CN&pass_ticket=%s' % (
        self.loginInfo['url'], self.loginInfo['pass_ticket'])
    data = {
        'BaseRequest'  : self.loginInfo['BaseRequest'],
        'Code'         : 3,
        'FromUserName' : self.storageClass.userName,
        'ToUserName'   : self.storageClass.userName,
        'ClientMsgId'  : int(time.time()), }
    headers = {
        'ContentType': 'application/json; charset=UTF-8',
        'User-Agent' : config.USER_AGENT, }
    r = self.s.post(url, data=json.dumps(data), headers=headers)
    return ReturnValue(rawResponse=r)

def start_receiving(self, exitCallback=None, getReceivingFnOnly=False,signal_m=None):
    self.alive = True
    def maintain_loop():
        retryCount = 0
        while self.alive:
            try:
                i = sync_check(self)
                if i is None:
                    self.alive = False
                elif i == '0':
                    pass
                else:
                    msgList, contactList = self.get_msg()
                    if msgList:
                        msgList = produce_msg(self, msgList)
                        signal_m(msgList)
                        '''
                        for msg in msgList:
                            self.msgList.put(msg)
                        '''
                    if contactList:
                        chatroomList, otherList = [], []
                        for contact in contactList:
                            if '@@' in contact['UserName']:
                                chatroomList.append(contact)
                            else:
                                otherList.append(contact)
                        chatroomMsg = update_local_chatrooms(self, chatroomList)
                        chatroomMsg['User'] = self.loginInfo['User']
                        self.msgList.put(chatroomMsg)
                        update_local_friends(self, otherList)
                retryCount = 0
            except requests.exceptions.ReadTimeout:
                pass
            except:
                retryCount += 1
                logger.error(traceback.format_exc())
                if self.receivingRetryCount < retryCount:
                    self.alive = False
                else:
                    time.sleep(1)
        self.logout()
        if hasattr(exitCallback, '__call__'):
            exitCallback()
        else:
            logger.info('LOG OUT!')
    if getReceivingFnOnly:
        return maintain_loop
    else:
        maintainThread = threading.Thread(target=maintain_loop)
        maintainThread.setDaemon(True)
        maintainThread.start()
def sync_check(self):
    url = '%s/synccheck' % self.loginInfo.get('syncUrl', self.loginInfo['url'])
    params = {
        'r'        : int(time.time() * 1000),
        'skey'     : self.loginInfo['skey'],
        'sid'      : self.loginInfo['wxsid'],
        'uin'      : self.loginInfo['wxuin'],
        'deviceid' : self.loginInfo['deviceid'],
        'synckey'  : self.loginInfo['synckey'],
        '_'        : self.loginInfo['logintime'], }
    headers = { 'User-Agent' : config.USER_AGENT }
    self.loginInfo['logintime'] += 1
    try:
        r = self.s.get(url, params=params, headers=headers, timeout=config.TIMEOUT)
    except requests.exceptions.ConnectionError as e:
        try:
            if not isinstance(e.args[0].args[1], BadStatusLine):
                raise
            # will return a package with status '0 -'
            # and value like:
            # 6f:00:8a:9c:09:74:e4:d8:e0:14:bf:96:3a:56:a0:64:1b:a4:25:5d:12:f4:31:a5:30:f1:c6:48:5f:c3:75:6a:99:93
            # seems like status of typing, but before I make further achievement code will remain like this
            return '2'
        except:
            raise
    r.raise_for_status()
    regx = r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}'
    pm = re.search(regx, r.text)
    if pm is None or pm.group(1) != '0':
        logger.debug('Unexpected sync check result: %s' % r.text)
        return None
    return pm.group(2)

def get_msg(self):
    url = '%s/webwxsync?sid=%s&skey=%s&pass_ticket=%s' % (
        self.loginInfo['url'], self.loginInfo['wxsid'],
        self.loginInfo['skey'],self.loginInfo['pass_ticket'])
    data = {
        'BaseRequest' : self.loginInfo['BaseRequest'],
        'SyncKey'     : self.loginInfo['SyncKey'],
        'rr'          : ~int(time.time()), }
    headers = {
        'ContentType': 'application/json; charset=UTF-8',
        'User-Agent' : config.USER_AGENT }
    r = self.s.post(url, data=json.dumps(data), headers=headers, timeout=config.TIMEOUT)
    dic = json.loads(r.content.decode('utf-8', 'replace'))
    if dic['BaseResponse']['Ret'] != 0: return None, None
    self.loginInfo['SyncKey'] = dic['SyncKey']
    self.loginInfo['synckey'] = '|'.join(['%s_%s' % (item['Key'], item['Val'])
        for item in dic['SyncCheckKey']['List']])
    return dic['AddMsgList'], dic['ModContactList']

def logout(self):
    if self.alive:
        url = '%s/webwxlogout' % self.loginInfo['url']
        params = {
            'redirect' : 1,
            'type'     : 1,
            'skey'     : self.loginInfo['skey'], }
        headers = { 'User-Agent' : config.USER_AGENT }
        self.s.get(url, params=params, headers=headers)
        self.alive = False
    self.isLogging = False
    self.s.cookies.clear()
    del self.chatroomList[:]
    del self.memberList[:]
    del self.mpList[:]
    return ReturnValue({'BaseResponse': {
        'ErrMsg': 'logout successfully.',
        'Ret': 0, }})
