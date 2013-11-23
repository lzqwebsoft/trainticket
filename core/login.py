# coding: utf8
import json
import threading
import urllib, urllib.request
from common.httpaccess import HttpTester
try:
    # Python2
    import ConfigParser as configparser
    from HTMLParser import HTMLParser
except ImportError:
    # Python3
    import configparser
    from html.parser import HTMLParser

# 读取URL获得验证码的路径HTML解析类
class LoginRandCodeParser(HTMLParser):
    def __init__(self):
        self.randCodeUrl=""
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and ('id', 'img_rrand_code') in attrs:
            for x in attrs:
                if x[0] == 'src':
                    self.randCodeUrl=x[1]
                    break

    def getRandCodeURL(self):
        return self.randCodeUrl

# 解释登录成功后的用户中心HTML
# <h1 class="text_16" >XXX先生 ，您好！</h1>
class InfoCenterParser(HTMLParser):
    def __init__(self):
        self.welcomeInfo=""
        self.flag = False
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'h1' and ('class', 'text_16') in attrs:
            self.flag = True

    def handle_data(self, data):
        if self.flag:
            self.welcomeInfo = data

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.flag = False

    def getWelcomeInfo(self):
        return self.welcomeInfo

def getContent(url, encode='gb18030'):
    try:
        response = urllib.request.urlopen(url)
        content = response.read().decode(encode, 'ignore')
        return content
    except Exception:
        return ''

def getRandImageUrl(ht):
    loginHtml = ht.get(url="https://dynamic.12306.cn/otsweb/loginAction.do", params={"method": "init"});
    loginParer = LoginRandCodeParser()
    loginParer.feed(loginHtml)
    randUrl = loginParer.getRandCodeURL()
    if randUrl:
        return "https://dynamic.12306.cn/otsweb/" + randUrl
        # randImage = ShowRandImage(randUrl)
        # randImage.show()
    else:
        f = open ("login.html", 'w')
        f.write(loginHtml)
        f.close()
        print("验证码URL获取失败")
    return None

def login(ht, username, password, randcode):
    # 创建一个线程用户显示验证码图片
    # showImageThread = threading.Thread(target=parserLoginHtmlShowRandImage, name="ShowImageThread")
    # showImageThread.setDaemon(1)
    # showImageThread.start()

    # 首先要请求 https://dynamic.12306.cn/otsweb/loginAction.do?method=loginAysnSuggest
    # 用户判断当前网络环境是否可以登录,从得到的JSON数据{"loginRand":"172","randError":"Y"}中
    # 获取登录令牌loginRand的值
    json_str = ht.get(url="https://dynamic.12306.cn/otsweb/loginAction.do", params={"method": "loginAysnSuggest"})
    json_data = json.loads(json_str);

    loginRand = 0
    if (json_data["randError"] != 'Y'):
        print("当前网络繁忙不可访问!")
    else:
        loginRand = json_data["loginRand"]
        # print("loginRand: " + str(loginRand))
        # 接收用户输入的验证码
        #randcode = input("验证码：")


        # MTE2MTYwMQ===OTRhMDI4MzQ2ZjdjN2YyZQ==
        # form_tk=null
        # isClick=
        # loginRand=792
        # loginUser.user_name=
        # myversion=undefined
        # nameErrorFocus=
        # passwordErrorFocus=
        # randCode=s49f
        # randErrorFocus=
        # refundFlag=Y
        # refundLogin=N
        # user.password=

        postDatas = {"loginRand": loginRand,
        "isClick": "",
        "nameErrorFocus": "",
        "passwordErrorFocus": "",
        "randErrorFocus": "",
        "loginUser.user_name": username,
        "form_tk": "null",
        "user.password": password,
        "randCode": randcode,
        "randErrorFocus": "",
        "myversion": "undefined",
        "refundFlag": "Y",
        "refundLogin": "N"}

        # print("logingRand %s, randcode: %s, username: %s, password: %s" % (loginRand, randcode, username, password))
        content = ht.post(url="https://dynamic.12306.cn/otsweb/loginAction.do?method=login", params=postDatas)

        infocenterParser = InfoCenterParser()
        infocenterParser.feed(content)

        welcomeInfo = infocenterParser.getWelcomeInfo()
        if welcomeInfo:
            print(welcomeInfo)
            return True
        else:
            f = open ("log_result.html", 'w')
            f.write(content)
            f.close()
            print("登录失败！")
    return False

def getUserInfo():
    config = configparser.SafeConfigParser()
    config.read("config.ini")
    try:
        username = config.get("UserInfo","username")
        password = config.get("UserInfo", "password")
    except configparser.NoSectionError:
        print("请设置登录信息的config.ini文件")
        input("\r\n输入任意字符结束...")
    else:
        if username.strip()!='' and password.strip()!='':
            return (username, password)
        else:
            print("请设置登录的用户名与密码")
            input("\r\n输入任意字符结束...")

    return None