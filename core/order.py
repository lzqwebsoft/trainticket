# coding: utf8
import json
import re
from common.httpaccess import HttpTester
from threading import Timer
try:
    # Python2
    from HTMLParser import HTMLParser
    # import tkMessageBox as messagebox
except ImportError:
    # Python3
    from html.parser import HTMLParser
    # from tkinter import messagebox

# 用于解析车票预订HTML的解析类
class ParserConfirmPassengerInitPage(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.train_info = []           # 列车信息
        self.current_seats = []        # 当前可用席别
        self.train_info_table_flag = False
        self.tr_flag = False
        self.seats_td_flag = False
        self.train_info_td_flag = False


        self.form_flag = False
        self.confirm_passenger_params = {}   # 隐藏hidden

        self.seats_types = {}                # 席别
        self.current_handle_value = ''
        self.seats_types_flag = False
        self.seats_types_option_flag = False

        self.ticket_types = {}               # 票种
        self.ticket_types_flag = False
        self.ticket_types_option_flag = False

        self.card_types = {}                 # 证件类型
        self.card_types_flag = False
        self.card_types_option_flag = False

        # 图片验证码URL
        self.img_rand_code_url = ''

        # 错误信息
        self.error_message = ''
        self.error_message_flag = False

    def handle_starttag(self, tag, attrs):
        # 所有form中hidden标签值
        if tag=='form' and ('name', 'save_passenger_single') in attrs and ('id', 'confirmPassenger') in attrs:
            self.form_flag = True
        if self.form_flag and tag == 'input' and ('type', 'hidden') in attrs:
            attrs = dict(attrs)
            if 'name' in attrs:
                self.confirm_passenger_params[attrs['name']] = ('value' in attrs and [attrs['value']] or [''])[0]

        # 席别的Value
        if self.form_flag and tag == 'select' and  ("name", "passenger_1_seat") in attrs and ('id', "passenger_1_seat") in attrs:
            self.seats_types_flag = True
        if self.seats_types_flag and tag == 'option':
            attrs = dict(attrs)
            if 'value' in attrs:
                self.seats_types[attrs['value']]=''
                self.handle_current_value = attrs['value']
                self.seats_types_option_flag = True

        # 票类的Value
        if self.form_flag and tag == 'select' and  ("name", "passenger_1_ticket") in attrs and ('id', "passenger_1_ticket") in attrs:
            self.ticket_types_flag = True
        if self.ticket_types_flag and tag == 'option':
            attrs = dict(attrs)
            if 'value' in attrs:
                self.ticket_types[attrs['value']]=''
                self.handle_current_value = attrs['value']
                self.ticket_types_option_flag = True

        # 证件类型的Value
        if self.form_flag and tag == 'select' and  ("name", "passenger_1_cardtype") in attrs and ('id', "passenger_1_cardtype") in attrs:
            self.card_types_flag = True
        if self.card_types_flag and tag == 'option':
            attrs = dict(attrs)
            if 'value' in attrs:
                self.card_types[attrs['value']]=''
                self.handle_current_value = attrs['value']
                self.card_types_option_flag = True

        # 当前列车信息标记
        if tag == 'table' and ('class', 'qr_box') in attrs and ('id', 'passenger_single_tb_id') not in attrs:
            self.train_info_table_flag = True
        if tag == 'tr':
            self.tr_flag = True
        if tag =='td' and len(attrs)==0:
            self.seats_td_flag = True
        if tag == 'td' and ('class', "bluetext") in attrs:
            self.train_info_td_flag = True

        # 验证码图片
        if tag == 'img' and ('id', 'img_rrand_code') in attrs:
            for x in attrs:
                if x[0] == 'src':
                    self.img_rand_code_url=x[1]
                    break

        # 错误信息
        if tag=="div" and ('class', 'error_text') in attrs:
            self.error_message_flag = True

    def handle_data(self, data):
        # 当前列车信息
        if self.train_info_table_flag and self.tr_flag and self.train_info_td_flag:
            self.train_info.append(data.strip())
        if self.train_info_table_flag and self.tr_flag and self.seats_td_flag:
            self.current_seats.append(data.strip())

        # 获取席别的Text
        if self.seats_types_option_flag and self.handle_current_value.strip()!='':
            self.seats_types[self.handle_current_value]=data.strip()
            self.handle_current_value=''

        # 获取票类型的Text
        if self.ticket_types_option_flag and self.handle_current_value.strip()!='':
            self.ticket_types[self.handle_current_value]=data.strip()
            self.handle_current_value=''

        # 证件类型的Text
        if self.card_types_option_flag and self.handle_current_value.strip()!='':
            self.card_types[self.handle_current_value]=data.strip()
            self.handle_current_value=''

        # 获取错误信息
        if self.error_message_flag:
            removeHTMLRe = re.compile(r'</?\w+[^>]*>', re.DOTALL)
            self.error_message = removeHTMLRe.sub("", data)

    def handle_endtag(self, tag):
        # 结束表单hidden标记
        if tag == 'form':
            self.form_flag = False

        # 结束列车信息标记
        if tag == 'table':
            self.train_info_table_flag = False
        if tag == 'tr':
            self.tr_flag = False
        if tag == 'td':
            self.train_info_td_flag = False
            self.seats_td_flag = False

        # 结束，席别，票类型，证件类型标记
        if tag == 'select':
            self.seats_types_flag = False
            self.ticket_types_flag = False
            self.card_types_flag = False
        if tag=='option':
            self.seats_types_option_flag = False
            self.ticket_types_option_flag = False
            self.card_types_option_flag = False

        # 错误信息
        if tag == 'div':
            self.error_message_flag = False

    def get_train_info(self):
        return self.train_info

    def get_current_seats(self):
        return self.current_seats

    def get_hidden_params(self):
        return self.confirm_passenger_params

    def get_seats_types(self):
        return self.seats_types

    def get_ticket_types(self):
        return self.ticket_types

    def get_card_types(self):
        return self.card_types

    def get_img_code_url(self):
        return "https://dynamic.12306.cn"+self.img_rand_code_url

    def get_error_message(self):
        return self.error_message


def submitOrderRequest(ht, selectStr=None, queryParams={}):
    if not selectStr and selectStr.strip()=='':
        print("预定数据为空")
    selectStr_arr = selectStr.split("#");
    if(len(selectStr_arr)!=14):
        print("无效的预定数据")
    station_train_code=selectStr_arr[0];
    lishi=selectStr_arr[1];
    starttime=selectStr_arr[2];
    trainno=selectStr_arr[3];
    from_station_telecode=selectStr_arr[4];
    to_station_telecode=selectStr_arr[5];
    arrive_time=selectStr_arr[6];
    from_station_name=selectStr_arr[7];
    to_station_name=selectStr_arr[8];
    from_station_no=selectStr_arr[9];
    to_station_no=selectStr_arr[10];
    ypInfoDetail=selectStr_arr[11];
    mmStr = selectStr_arr[12];
    locationCode = selectStr_arr[13];

    # 查询条件参数的整理
    train_date=queryParams['train_date']
    include_student="00"
    from_station_telecode_name=queryParams['from_station']
    to_station_telecode_name=queryParams['to_station']
    single_round_type=1
    if single_round_type==1:
        round_train_date=queryParams['train_date']
        round_start_time_str=queryParams['start_time']
    elif single_round_type==2:
        round_train_date = queryParams['round_train_date']
        round_start_time_str= queryParams['round_start_time_str']
    train_pass_type=queryParams['trainPassType']
    train_class_arr=queryParams['trainClass']
    start_time_str=queryParams['start_time']

    submitUrl = "https://dynamic.12306.cn/otsweb/order/querySingleAction.do?method=submutOrderRequest"
    submitParams = {
        "station_train_code" : station_train_code,
        "train_date": train_date,                                  # 列车时间
        "seattype_num": '',                                        # 席别
        "from_station_telecode": from_station_telecode,
        "to_station_telecode": to_station_telecode,
        "include_student": include_student,                        # 学生票
        "from_station_telecode_name": from_station_telecode_name,  # 查询框从哪里值
        "to_station_telecode_name": to_station_telecode_name,      # 查询框到哪里值
        "round_train_date": round_train_date,                      # 返程时间这里如果没有则有出发时间
        "round_start_time_str": round_start_time_str,              # 返程时间段
        "single_round_type": single_round_type,                    # 单程1，返程2
        "train_pass_type": train_pass_type,                        # 列车通过类型
        "train_class_arr": train_class_arr,                        # 列车类型
        "start_time_str": start_time_str,                          # 开始时间段
        # 获取具体车次的值
        "lishi": lishi,
        "train_start_time": starttime,
        "trainno4": trainno,
        "arrive_time": arrive_time,
        "from_station_name": from_station_name,
        "to_station_name": to_station_name,
        "from_station_no": from_station_no,
        "to_station_no": to_station_no,
        "ypInfoDetail": ypInfoDetail,
        "mmStr": mmStr,
        "locationCode": locationCode,
        "myversion": "undefined"               # 未知参数
    }
    # 请求预定操作，执行后页面会重定向
    submitResult= ht.post(url=submitUrl, params=submitParams)

    f = open("submitResult.html", 'w')
    f.write(submitResult)
    f.close()

    return submitResult
    # 重定向页面URL，即乘客信息合核对页面
    #    https://dynamic.12306.cn/otsweb/order/confirmPassengerAction.do?method=init
    # redirctorContent = ht.get(url="https://dynamic.12306.cn/otsweb/order/confirmPassengerAction.do", params={"method": "init"})

# 联系人JSON数据URL：
#    https://dynamic.12306.cn/otsweb/order/confirmPassengerAction.do?method=getpassengerJson：
def getAllContacts(ht):
    contactsUrl = "https://dynamic.12306.cn/otsweb/order/confirmPassengerAction.do"
    params=[('method', 'getpassengerJson')]
    resultContent = ht.get(url=contactsUrl, params=params)
    if resultContent and resultContent.strip()!='':
        jsonData = json.loads(resultContent)
        if 'passengerJson' in jsonData and len(jsonData['passengerJson'])>0:
            return jsonData['passengerJson']
        else:
            print("未查找到常用联系人")
    return []

# 判断获取预定画面信息
def getInfoMessage(submitResult=''):
    messageRe = re.compile(r'var message\s*?=\s*?[\'\"](.+?)[\'\"];', re.DOTALL)
    message = ''
    collects = messageRe.findall(submitResult)
    if len(collects)==1:
        message = collects[0]
    return message

# 模拟:submit_form_confirm，用于检测乘客输入值的正确性与否
# JS URL: https://dynamic.12306.cn/otsweb/js/order/save_passenger_info.js
# POST提交至：https://dynamic.12306.cn/otsweb/order/confirmPassengerAction.do?method=checkOrderInfo&rand=a6ud
# rand 为输入的验证码
def checkOrderInfo(ht, params=None, rand=""):
    if not params or len(params)<=0:
        print("参数不能为空")
        return False
    checked_result_json_str = ht.post(url="https://dynamic.12306.cn/otsweb/order/confirmPassengerAction.do?method=checkOrderInfo&rand="+rand, params=params)
    checked_result_json = json.loads(checked_result_json_str)
    if 'errMsg' in checked_result_json and 'Y' != checked_result_json['errMsg']:
        print(checked_result_json['errMsg'])
        return False
    elif 'checkHuimd' in checked_result_json and 'N' == checked_result_json['checkHuimd']:
        # 对不起，由于您取消次数过多，今日将不能继续受理您的订票请求！
        print(checked_result_json['msg'])
        return False
    elif 'check608' in checked_result_json and 'N' == checked_result_json['check608']:
        # 本车为实名制列车，实行一日一车一证一票制！
        print(checked_result_json['msg'])
        return False
    else:
        return True

# 模拟查询当前的列车排队人数的方法
# 返回信息组成的提示字符串
# params:
# train_date=2013-11-13
# train_no=550000K35190
# station=K351
# seat=1
# from=SNH
# to=WCN
# ticket=1014853031404155000010148500003026350000
# GET提交: https://dynamic.12306.cn/otsweb/order/confirmPassengerAction.do?method=getQueueCount
# 结果：{"countT":0,"count":0,"ticket":"1*****30314*****00001*****00003*****0000","op_1":false,"op_2":false}
def getQueueCount(ht, params=None, seat_type=None):
    if not params or len(params)<=0:
        print("参数不能为空")
        return ''
    submitParams = [('method', 'getQueueCount')]
    submitParams.extend(params)
    json_str = ht.get(url="https://dynamic.12306.cn/otsweb/order/confirmPassengerAction.do", params=submitParams)
    json_data = json.loads(json_str)
    if 'ticket' not in json_data:
        print("获取排队人数失败")
        return ''
    queue_note = "尊敬的旅客，本次列车您选择的席别尚有余票" + getTicketCountDesc(json_data['ticket'], seat_type) + "，"
    if 'op_2' in json_data and json_data['op_2']:
        queue_note += "目前排队人数已经超过余票张数，请您选择其他席别或车次，特此提醒。"
    else:
        # 这里放开弹出窗体的确定按钮，充许预定
        if 'countT' in json_data and json_data['countT'] > 0 :
            queue_note += "目前排队人数" + str(data.countT) + "人，"
        queue_note += "特此提醒。"
    queue_note += "\n请确认订单信息是否正确，如正确请点击“确定”，系统将为您随机分配席位。"
    return queue_note

# 计算指定席别的余票数
# mark: 1*****30314*****00001*****00003*****0000
def getTicketCountDesc(mark, seat_type):
    rt = ""
    seat_1 = -1
    seat_2 = -1
    i = 0
    while i < len(mark):
        s = mark[i:10+i]
        c_seat = s[0:1]
        if c_seat == seat_type:
            count = s[6:10]
            while len(count) > 1 and count[0:1] == "0" :
                count = count[1:]
            count = int(count)
            if count < 3000:
                seat_1 = count
            else:
                seat_2 = count - 3000
        i = i + 10;
    if seat_1 > -1 :
        rt += " %s 张" % seat_1
    if seat_2 > -1 :
        rt += ", 无座 %s 张" % seat_2
    return rt

# 模拟点击订单的确定按钮实现提交,检查是否可以排队获取订单
# 参数tourFlag为旅程形式
def checkQueueOrder(ht, tourFlag, params=None):
    # messagebox.showinfo("交易提示", "您也可点击 未完成订单，查看订单处理情况。")
    url = 'https://dynamic.12306.cn/otsweb/order/'
    if tourFlag == 'dc':
        # 异步下单-单程
        url += 'confirmPassengerAction.do?method=confirmSingleForQueue'
    elif tourFlag == 'wc':
        # 异步下单-往程
        url += 'confirmPassengerAction.do?method=confirmPassengerInfoGoForQueue'
    elif tourFlag == 'fc':
        # 异步下单-返程
        url += 'confirmPassengerAction.do?method=confirmPassengerInfoBackForQueue'
    elif tourFlag == 'gc':
        # 异步下单-改签
        url += 'confirmPassengerResignAction.do?method=confirmPassengerInfoResignForQueue'
    else:
        print("下单失败！旅程形式为" + tourFlag)
        return False
    print("正在处理，请稍候。")
    json_str = ht.post(url=url, params=params)
    json_data = json.loads(json_str)
    if 'errMsg' in json_data and json_data['errMsg'] != 'Y':
        print("出票失败，" + json_data['errMsg'] + "请重新选择。")
        return False
    else:
        return True

# 订单排队等待时间
class OrderQueueWaitTime:

    def __init__(self, ht, tourFlag, waitMethod, finishMethod):
        self.tourFlag = tourFlag
        self.waitMethod = waitMethod
        self.finishMethod = finishMethod
        
        self.dispTime = 1
        self.nextRequestTime = 1
        self.isFinished = False
        self.waitObj = None

        self.ht = ht

    def start(self):
        Timer(1.0, self.timerJob).start()

    def timerJob(self):
        if self.isFinished:
            return

        if self.dispTime <= 0:
            self.isFinished = True
            self.finishMethod(self.tourFlag, self.dispTime, self.waitObj);
            return
        
        if self.dispTime == self.nextRequestTime:
            self.getWaitTime()

        second = self.dispTime
        show_time = ""
        minute = int(second / 60);
        if minute >= 1:
            show_time = minute + "分"
            second = second % 60;
        else:
            show_time = "1分"

        dispTime = 1
        if self.dispTime > 1:
            self.dispTime -= 1
            dispTime = self.dispTime
        self.waitMethod(self.tourFlag, dispTime, show_time)
        # 等待1秒后继续执行
        Timer(1.0, self.timerJob).start()

    def getWaitTime(self):
        params = [('method', 'queryOrderWaitTime'), ('tourFlag', self.tourFlag)]
        url = 'https://dynamic.12306.cn/otsweb/order/myOrderAction.do'
        json_str = self.ht.get(url=url, params=params)
        if json_str and json_str.strip()!=0:
            json_data = json.loads(json_str)
            self.waitObj = json_data
            self.dispTime = json_data['waitTime']

            flashWaitTime = int(json_data['waitTime']/1.5)
            if flashWaitTime > 60:
                flashWaitTime = 60
            else:
                flashWaitTime = flashWaitTime
            nextTime = json_data['waitTime'] - flashWaitTime;
            if nextTime<=0:
                self.nextRequestTime = 1
            else:
                self.nextRequestTime = nextTime

def waitFunc(tourFlag, return_time, show_time) :
    if return_time <= 5 :
        print("您的订单已经提交，系统正在处理中，请稍等。")
    elif return_time > 30 * 60 :
        print("您的订单已经提交，预计等待时间超过30分钟，请耐心等待。")
    else:
        print("您的订单已经提交，最新预估等待时间" + show_time + "，请耐心等待。")

# 跳转-单程
def finishMethod(tourFlag, time, returnObj, params=None):
    if time == -1 :
        action_url = "https://dynamic.12306.cn/otsweb/order/";
        if tourFlag == 'dc':
            # 异步下单-单程
            action_url = "confirmPassengerAction.do?method=payOrder&orderSequence_no=" + returnObj['orderId'];
        elif tourFlag == 'wc' :
            # 异步下单-往程
            action_url = "confirmPassengerAction.do?method=wcConfirm&orderSequence_no=" + returnObj['orderId']
        elif tourFlag == 'fc':
            # 异步下单-返程
            action_url = "confirmPassengerAction.do?method=backPay&orderSequence_no=" + returnObj['orderId']
        elif tourFlag == 'gc':
            # 异步下单-改签
            action_url = "confirmPassengerResignAction.do?method=resignPay&orderSequence_no=" + returnObj['orderId']
        #ht.post(url=action_url, params=params)
        # 处理订单提交成功操作
        print('车票预定成功订单号为：%s，请立即打开浏览器登录12306，访问‘未完成订单’在45分钟内完成支付！' % returnObj['orderId'])
        pass
    else:
        procFail(time, returnObj)

# 订单提交失败
def procFail(flag, returnObj):
    renewURL = "<a href='https://dynamic.12306.cn/otsweb/order/querySingleAction.do?method=init'>[重新购票]</a>"
    my12306URL = "<a href='https://dynamic.12306.cn/loginAction.do?method=initForMy12306'>[我的12306]</a>"
    if flag == -1:
        return;
    elif flag == -2:
        if returnObj['errorcode'] == 0:
            print("占座失败，原因:" + returnObj['msg'] + " 请访问" + my12306URL + ",办理其他业务.")
        else:
            print("占座失败，原因:" + returnObj['msg'] + " 请访问" + renewURL + ",重新选择其它车次.")
    elif flag == -3 :
        print("订单已撤销 请访问" + renewURL + ",重新选择其它车次.")
    else:
        # 进入未完成订单页面
        # url = "https://dynamic.12306.cn/otsweb/order/myOrderAction.do?method=queryMyOrderNotComplete&leftmenu=Y&fakeParent=true";
        pass

def main():
    f = open ("./resources/order/confirm_passenger_init.html", 'r', encoding="utf-8")
    submitResult = f.read()
    f.close()

    parser = ParserConfirmPassengerInitPage()
    parser.feed(submitResult)

    f = open('hend_params.txt', 'w')
    f.write(str((parser.get_hidden_params()).items()))
    f.close()

if __name__ == '__main__':
    main()
