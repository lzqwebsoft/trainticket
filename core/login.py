# coding: utf8
import json
import configparser
import html.parser
import urllib, urllib.request, urllib.parse

# 读取URL获得验证码的路径HTML解析类
class LoginRandCodeParser(html.parser.HTMLParser):
    def __init__(self):
        self.randCodeUrl = ""
        self.rand = ''
        html.parser.HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and ('id', 'img_rand_code') in attrs:
            tag_attrs = dict(attrs)
            if 'src' in tag_attrs and tag_attrs['src']:
                # 登录验证码的相对路径
                relative_path = tag_attrs['src']
                # 完整路径
                self.randCodeUrl = "https://kyfw.12306.cn" + relative_path
                img_code_params = urllib.parse.parse_qs(relative_path)
                if 'rand' in img_code_params:
                    # 登录验证码的验证令牌
                    self.rand = img_code_params['rand'][0] if img_code_params['rand'] else ''

# 解析登录后返回的HTML, 获取用户帐户信息
# 用于判断用户是否成功登录
class InfoCenterParser(html.parser.HTMLParser):
    def __init__(self):
        self.account_name = ""
        self.user_info_link = False
        self.flag = False
        html.parser.HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag == 'a' and ('id', 'login_user') in attrs:
            self.user_info_link = True
        if tag == 'span' and self.user_info_link:
            self.flag = True

    def handle_data(self, data):
        if self.user_info_link and self.flag:
            self.account_name = data

    def handle_endtag(self, tag):
        if tag == 'a':
            self.user_info_link = False
        if tag == 'span':
            self.flag = False

# 获取验证码图片
def getRandImageUrlAndCodeRand(ht):
    result = {'url': '', 'rand': ''}
    # 得到登录页面HTML内容
    loginHtml = ht.get(url="https://kyfw.12306.cn/otn/login/init")
    # 解析登录页面内容，获取图片验证码的URL地址，以及验证码令牌rand
    loginParer = LoginRandCodeParser()
    loginParer.feed(loginHtml)
    randUrl = loginParer.randCodeUrl
    rand = loginParer.rand
    if randUrl and rand:
        result['url'] = randUrl
        result['rand'] = rand
        return result
    else:
        f = open("login.html", 'w', encoding='utf-8')
        f.write(loginHtml)
        f.close()
        print("验证码URL获取失败, 详情查看返回的login.html页面")
    return result


def login(ht, username, password, randCode, rand, check_rand_status='Y'):
    # 判断用户是否进行验证码的检查操作，如果check_rand_status为N则直接跳过进行登录
    if check_rand_status == 'Y':
        # 判断用户输入的验证码是否正确
        post_datas = {
            'randCode': randCode, # 输入验证码
            'rand': rand            # 验证令牌
        }
        # 检证输入验证码的合法性
        json_str = ht.post(url="https://kyfw.12306.cn/otn/passcodeNew/checkRandCodeAnsyn", params=post_datas)
        json_data = json.loads(json_str)
    else:
        json_data = {'data': 'Y'}

    if (json_data["data"] == 'Y'):
        post_data = {
            "loginUserDTO.user_name": username,
            "userDTO.password": password,
            "randCode": randCode
        }
        # 请求 https://kyfw.12306.cn/otn/login/loginAysnSuggest
        # 用于判断当前网络环境是否可以登录,得到JSON数据：
        # {"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":"Y","messages":[],"validateMessages":{}}
        json_str = ht.post(url="https://kyfw.12306.cn/otn/login/loginAysnSuggest", params=post_data)
        json_data = json.loads(json_str)

        # loginRand = 0
        # 检查用户是否可以登录
        if ("data" in json_data and json_data["data"] and "loginCheck" in json_data["data"] and json_data["data"][
            "loginCheck"] == 'Y'):
            # 用户登录，获取登录返回的HTML
            content = ht.post(url="https://kyfw.12306.cn/otn/login/userLogin", params=post_data)
            # 解析登录返回的HTML判断用户是否成功登录
            infocenterParser = InfoCenterParser()
            infocenterParser.feed(content)
            user_info = infocenterParser.account_name
            if user_info:
                print('您好, %s' % user_info)
                return True
            else:
                f = open("login_result.html", 'w', encoding='utf-8', errors='ignore')
                f.write(content)
                f.close()
                print("登录失败, 详情查看登录返回的login_result.html页面")
        else:
            messages = json_data.get('messages', '') if type(json_data) == dict else json_str
            if not messages: messages = '当前网络繁忙不可登录访问!'
            print(messages)
    else:
        print(json_str)
        print('输入的验证码有误.')

    return False

# 读取config.ini文件获取用户设置的帐号信息
def getUserInfo():
    config = configparser.ConfigParser()
    config.read("config.ini")
    try:
        username = config.get("UserInfo", "username")
        password = config.get("UserInfo", "password")
    except configparser.NoSectionError:
        print("请设置登录信息的config.ini文件")
        input("\r\n输入任意字符结束...")
    else:
        if username.strip() != '' and password.strip() != '':
            return (username, password)
        else:
            print("请设置登录的用户名与密码")
            input("\r\n输入任意字符结束...")

    return None

# 读取config.ini文件获取系统性配置信息
def getPerformanceInfo():
    config = configparser.ConfigParser()
    config.read("config.ini")
    try:
        performanceInfo = dict(config.items("PerformanceInfo"))
        return performanceInfo
    except configparser.NoSectionError:
        print("系统性能配置装载失败!")
    return {}

def getGoAgentHost():
    config = configparser.ConfigParser()
    config.read("config.ini")
    try:
        host = dict(config.items("GoAgentHost"))
        return host
    except configparser.NoSectionError:
        print("未设定代理服务器!")
    return {}