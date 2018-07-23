import os, platform
dist='dist'
QRIMG='QR.png'
SelfIMG='self'
Self_Image_Path=os.path.join(dist,SelfIMG)
Self_Image_Width=100
Self_Image_Height=100
VERSION = '1.3.10'
BASE_URL = 'https://login.weixin.qq.com'
OS = platform.system() # Windows, Linux, Darwin
DIR = os.getcwd()
DEFAULT_QR = os.path.join(dist,QRIMG)
QR_width=210
QR_height=210
TIMEOUT = (10, 60)
pleaselogin="please login on mobile"
qrreset="QR has reset"
updatedata="Updating QR"

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'
