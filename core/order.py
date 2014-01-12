# coding: utf8
import json
import re
import time
import urllib.parse
# Python3
import html.parser
from threading import Timer
# from tkinter import messagebox

# 用于解析车票预订HTML的解析类
class ParserConfirmPassengerInitPage(html.parser.HTMLParser):
    def __init__(self, orderInitHtml=''):
        html.parser.HTMLParser.__init__(self)
        self.orderInitHtml = orderInitHtml

        self.train_info = []                       # 当前列车信息
        self.order_request_params = {}             # 订单提交时的参数
        self.current_seats = {}                    # 席别信息
        self.img_rand_code_url = ''                # 图片验证码URL
        self.img_rand_code_rand = ''               # 图片验证码随机数
        self.ticketInfoForPassengerForm = {}  # 初始化当前页面参数

        train_info_re = re.compile(r'var ticketInfoForPassengerForm=(\{.+\})?;')
        if orderInitHtml and train_info_re.search(orderInitHtml):
            collects = train_info_re.findall(orderInitHtml)
            train_info_str = collects[0]
            if train_info_str:
                self.ticketInfoForPassengerForm = json.loads(train_info_str.replace("'", '"'))
                self._parse_train_info()

        order_request_re = re.compile(r'var orderRequestDTO=(\{.+\})?;')
        if orderInitHtml and order_request_re.search(orderInitHtml):
            collects = order_request_re.findall(orderInitHtml)
            order_request_str = collects[0]
            if order_request_str:
                self.order_request_params = json.loads(order_request_str.replace("'", '"'))

        self.train_info_flag = False
        self.train_info_str = ''

        self.globalRepeatSubmitToken = ''
        token_re = re.compile(r'var globalRepeatSubmitToken[ ]*?=[ ]*?([\"\'])(.+)?\1;')
        if orderInitHtml and token_re.search(orderInitHtml):
            collects = token_re.findall(orderInitHtml)
            self.globalRepeatSubmitToken = collects[0][1] if collects and len(collects) > 0 else ''

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == 'img' and ('id', 'img_rand_code') in attrs:
            self.img_rand_code_url = attrs_dict['src']
            if self.img_rand_code_url and self.img_rand_code_url.strip():
                img_code_params = urllib.parse.parse_qs(self.img_rand_code_url)
                if 'rand' in img_code_params:
                    self.img_rand_code_rand = img_code_params['rand'][0] if img_code_params['rand'] else ''

    def handle_data(self, data):
        if self.train_info_flag and data:
            self.train_info_str += data.strip()

    def handle_endtag(self, tag):
        if tag == 'div':
            self.train_info_flag = False

    def get_train_info(self):
        return self.train_info

    def get_order_request_params(self):
        return self.order_request_params

    def get_ticketInfoForPassengerForm(self):
        return self.ticketInfoForPassengerForm

    # 由页面参数获取列车信息
    def _parse_train_info(self):
        av = self.ticketInfoForPassengerForm['queryLeftNewDetailDTO']
        aw = self.ticketInfoForPassengerForm['queryLeftTicketRequestDTO']
        train_date = time.strptime(aw['train_date'], '%Y%m%d')
        date = time.strftime('%Y-%m-%d', train_date)
        weeks_dict = ('周日', "周一", "周二", "周三", '周四', '周五', '周六')
        week = weeks_dict[int(time.strftime('%w', train_date))]
        station_train_code = av['station_train_code']
        # train_headers = aw['train_headers']
        lishi = aw['lishi']
        from_station_name = av['from_station_name']
        start_time = av['start_time'][:2] + ":" + av['start_time'][2:]
        to_station_name = av['to_station_name']
        arrive_time = av['arrive_time'][:2] + ":" + av['arrive_time'][2:]
        self.train_info = (
            "%s（%s）" % (date, week),
            "%s次" % station_train_code,
            "%s站 （%s）开" % (from_station_name, start_time),
            "%s站 （%s）到" % (to_station_name, arrive_time),
            "历时 （%s）" % lishi
        )

    def get_img_code_url(self):
        return "https://kyfw.12306.cn" + self.img_rand_code_url

    def get_img_code_rand(self):
        return self.img_rand_code_rand


# 提交用户预订请求，得到提交后的JSON
def submitOrderRequest(ht, selectStr=None, queryParams={}):
    submitResult = ''
    if not selectStr or not selectStr.strip():
        print("预定数据为空")
        return submitResult
        # 检查用户的合法性
    checkUserUrl = 'https://kyfw.12306.cn/otn/login/checkUser'
    checkUserResult = ht.post(url=checkUserUrl, headers={'If-Modified-Since': 0, 'Cache-Control': 'no-cache'})
    check_result_json = json.loads(checkUserResult)
    if 'data' in check_result_json and 'flag' in check_result_json['data'] and check_result_json['data']['flag']:
        checkusermdId = check_result_json['attributes'] if 'attributes' in check_result_json and check_result_json[
            'attributes'] else 'undefined'

        # 查询条件参数的整理
        train_date = queryParams['train_date']
        purpose_codes = 'ADULT'
        tour_flag = 'dc'
        query_from_station_name = queryParams['from_station']
        query_to_station_name = queryParams['to_station']
        back_train_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))

        submitUrl = "https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest"
        # 预定的请求参数，注意参数顺序
        # 注意这里为了防止secretStr被urllib.parse过度编码，在这里进行一次解码
        # 否则调用HttpTester类的post方法将会将secretStr编码成为无效码,造成提交预定请求失败
        submitParams = [
            ('secretStr', urllib.parse.unquote(selectStr)), # 预订提交令牌
            ('train_date', train_date), # 车票日期
            ('back_train_date', back_train_date), # 返程日期，没有则为当前日期
            ('tour_flag', tour_flag), # 旅行类型，单程dc,与返程fc
            ('purpose_codes', purpose_codes), # 标记是否为成人(ADULT)与学生(0X00)
            ('query_from_station_name', query_from_station_name), # 发站名称，汉字
            ('query_to_station_name', query_to_station_name)      # 到站名称，汉字
        ]
        if checkusermdId != 'undefined':
            submitParams.append(('_json_att', checkusermdId))

        # 请求预定操作，执行后页面会重定向
        submitResult = ht.post(url=submitUrl, params=submitParams)
        json_data = json.loads(submitResult)
        if 'status' in json_data and json_data['status']:
            if tour_flag == 'dc':
                submitResult = getOrderInitHtml(ht)
                return submitResult
        else:
            if 'messages' in json_data and json_data['messages']:
                print('预订失败：%s\r\n%s' % (json_data['messages'], submitParams))
            else:
                print('预订失败：%s' % submitResult)
    else:
        if 'messages' in check_result_json and check_result_json['messages']:
            print('验证用户合法性失败：%s' % check_result_json['messages'])
        else:
            print('验证用户合法性失败：%s' % checkUserResult)

    return submitResult


def getOrderInitHtml(ht):
    submitResult = ht.post(url='https://kyfw.12306.cn/otn/confirmPassenger/initDc')
    f = open("submitResult.html", 'w', encoding='utf-8')
    f.write(submitResult)
    f.close()
    return submitResult

# 获取设定的所有常用联系人信息
# https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs
def getAllContacts(ht):
    contactsUrl = "https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs"
    resultContent = ht.post(url=contactsUrl)
    if resultContent and resultContent.strip():
        jsonData = json.loads(resultContent)
        if 'data' in jsonData and jsonData['data'] and 'normal_passengers' in jsonData['data'] and jsonData['data'][
            'normal_passengers']:
            return jsonData['data']['normal_passengers']
        else:
            if 'data' in jsonData and 'exMsg' in jsonData['data'] and jsonData['data']['exMsg']:
                print(jsonData['data']['exMsg'])
            elif 'messages' in jsonData and jsonData['messages']:
                print(jsonData['messages'])
            else:
                print("未查找到常用联系人")
    return []

# 判断获取预定画面信息
def getInfoMessage(submitResult=''):
    messageRe = re.compile(r'var message\s*?=\s*?[\'\"](.+?)[\'\"];', re.DOTALL)
    message = ''
    collects = messageRe.findall(submitResult)
    if len(collects) == 1:
        message = collects[0]
    return message

# POST提交至：https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest
# rand 为输入的验证码令牌
# https://kyfw.12306.cn/otn/passcodeNew/checkRandCodeAnsyn
def checkOrderImgCode(ht, img_code='', rand="", token = ''):
    if not img_code:
        print("订单验证码不能为空")
        return False

    params ={
        'rand': rand,
        'randCode': img_code,
        'REPEAT_SUBMIT_TOKEN':token
    }
    checked_result_json_str = ht.post(url="https://kyfw.12306.cn/otn/passcodeNew/checkRandCodeAnsyn", params=params)
    checked_result_json = json.loads(checked_result_json_str)
    if 'status' in checked_result_json and checked_result_json['status'] and 'data' in checked_result_json and checked_result_json['data']!='N':
        return True
    else:
        if 'messages' in checked_result_json and checked_result_json['messages']:
            print(checked_result_json['messages'])
        else:
            print(checked_result_json_str)
            print('订单提交验证码输入有误')
        return False

# 模拟订单提交，用于检测乘客输入值的正确性与否
def checkOrderInfo(ht, randCode='', passengerTicketStr='', oldPassengersStr='', tour_flag='dc', token = ''):
    check_info = {}
    if passengerTicketStr and oldPassengersStr:
        params = {
            'cancel_flag': 2,
            'bed_level_order_num': '000000000000000000000000000000',
            'randCode': randCode,
            'passengerTicketStr': passengerTicketStr,
            'oldPassengerStr': oldPassengersStr,
            'tour_flag': tour_flag,
            'REPEAT_SUBMIT_TOKEN':token
        }
        check_result = ht.post(url='https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo', params=params)
        check_result_json = json.loads(check_result)
        # {"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":{"submitStatus":true},"messages":[],"validateMessages":{}}
        if 'status' in check_result_json and check_result_json['status']:
            submit_data = check_result_json['data'] if 'data' in check_result_json else {}
            if  'submitStatus' in submit_data and submit_data['submitStatus']:
                if 'get608Msg' in submit_data and submit_data['get608Msg']:
                    print('警告: %s' % submit_data['get608Msg'])
                check_info['isCheckOrderInfo'] = submit_data.get('isCheckOrderInfo', '')
                check_info['doneHMD'] = submit_data.get('doneHMD', '')
            else:
                if 'errMsg' in submit_data and submit_data['errMsg']:
                    print(submit_data['errMsg'])
                else:
                    print('出票失败!')
        else:
            if 'messages' in check_result_json and check_result_json['messages']:
                print(check_result_json['messages'])
            else:
                print(check_result)
                print('订单信息输入有误')
    else:
        print('输入的乘客信息不能为空')
    return check_info

# 模拟查询当前的列车排队人数的方法
# 返回信息组成的提示字符串
# params:
# train_date: new Date(orderRequestDTO.train_date.time).toString(),  # 列车日期
# train_no: orderRequestDTO.train_no,                           # 列车号
# stationTrainCode: orderRequestDTO.station_train_code,
# seatType: limit_tickets[0].seat_type,                         # 座位类型
# fromStationTelecode: orderRequestDTO.from_station_telecode,   # 发站编号
# toStationTelecode: orderRequestDTO.to_station_telecode,       # 到站编号
# leftTicket: ticketInfoForPassengerForm.queryLeftTicketRequestDTO.ypInfoDetail,
# purpose_codes: n,      # 默认取ADULT,表成人
# isCheckOrderInfo: m    # 检证乘客信息返回的令牌
# GET提交: https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount
# 结果：{"countT":0,"count":0,"ticket":"1*****30314*****00001*****00003*****0000","op_1":false,"op_2":false}
def getQueueCount(ht, params=None, seat_type=None):
    if not params or len(params) <= 0:
        print("参数不能为空")
        return ''
    submitParams = [('method', 'getQueueCount')]
    submitParams.extend(params)
    json_str = ht.post(url="https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount", params=submitParams)
    json_data = json.loads(json_str)
    queue_note = ''
    if 'status' in json_data and json_data['status']:
        json_data = json_data['data'] if 'data' in json_data else {}
        if 'ticket' not in json_data:
            print(json_str)
            print("获取排队人数失败")
            return ''
        queue_note = "尊敬的旅客，本次列车您选择的席别尚有余票" + getTicketCountDesc(json_data['ticket'], seat_type) + "，"
        if 'op_2' in json_data and json_data['op_2']:
            queue_note += "目前排队人数已经超过余票张数，请您选择其他席别或车次，特此提醒。"
        else:
            # 这里放开弹出窗体的确定按钮，充许预定
            if 'countT' in json_data and json_data['countT'] > 0:
                queue_note += "目前排队人数" + str(json_data['countT']) + "人，"
            queue_note += "特此提醒。"
        queue_note += "\n请确认订单信息是否正确，如正确请点击“确定”，系统将为您随机分配席位。"
    else:
        if 'messages' in json_data and json_data['messages']:
            print(json_data['messages'])
            return ''
        else:
            print(json_str)
            print("获取排队人数失败")
            return ''
    return queue_note

# 计算指定席别的余票数
# mark: 1*****30314*****00001*****00003*****0000
def getTicketCountDesc(mark, seat_type):
    rt = ""
    seat_1 = -1
    seat_2 = -1
    i = 0
    while i < len(mark):
        s = mark[i:10 + i]
        c_seat = s[0:1]
        if c_seat == seat_type:
            count = s[6:10]
            while len(count) > 1 and count[0:1] == "0":
                count = count[1:]
            count = int(count)
            if count < 3000:
                seat_1 = count
            else:
                seat_2 = count - 3000
        i = i + 10;
    if seat_1 > -1:
        rt += " %s 张" % seat_1
    if seat_2 > -1:
        rt += ", 无座 %s 张" % seat_2
    return rt

# 模拟点击订单的确定按钮实现提交,检查是否可以排队获取订单
# 参数tourFlag为旅程形式
def checkQueueOrder(ht, tourFlag, params=None):
    url = 'https://kyfw.12306.cn/otn/'
    if tourFlag == 'dc':
        # 异步下单-单程
        url += 'confirmPassenger/confirmSingleForQueue'
    elif tourFlag == 'wc':
        # 异步下单-往程
        url += 'confirmPassenger/confirmGoForQueue'
    elif tourFlag == 'fc':
        # 异步下单-返程
        url += 'confirmPassenger/confirmBackForQueue'
    elif tourFlag == 'gc':
        # 异步下单-改签
        url += 'confirmPassenger/confirmResignForQueue'
    else:
        print("下单失败！旅程形式为" + tourFlag)
        return False
    print("正在处理，请稍候。")
    json_str = ht.post(url=url, params=params)
    json_data = json.loads(json_str)
    if 'status' in json_data and json_data['status']:
        json_data = json_data['data'] if 'data' in json_data else {}
        if 'submitStatus' in json_data and json_data['submitStatus']:
            return True
        else:
            if 'errMsg' in json_data and json_data['errMsg']:
                print("出票失败，" + json_data['errMsg'] + "请重新选择。")
            else:
                print(json_str)
                print('订票失败!很抱歉,请重试提交预订功能!')
    else:
        if 'messages' in json_data and json_data['messages']:
            print('订票失败!'+ json_data['messages'])
        else:
            print(json_str)
            print('订票失败!很抱歉,请重试提交预订功能!')
    return False

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
            self.finishMethod(self.tourFlag, self.dispTime, self.waitObj)
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
        params = [('tourFlag', self.tourFlag)]
        url = 'https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime'
        json_str = self.ht.get(url=url, params=params)
        if json_str and json_str:
            json_data = json.loads(json_str)
            json_data = json_data['data'] if 'data' in json_data else {}
            if 'queryOrderWaitTimeStatus' in json_data and json_data['queryOrderWaitTimeStatus']:
                self.waitObj = json_data
                self.dispTime = json_data['waitTime']

                flashWaitTime = int(json_data['waitTime'] / 1.5)
                flashWaitTime = 60 if flashWaitTime > 60 else flashWaitTime

                nextTime = json_data['waitTime'] - flashWaitTime
                self.nextRequestTime = 1 if nextTime <= 0 else nextTime


def waitFunc(tourFlag, return_time, show_time):
    if return_time <= 5:
        print("您的订单已经提交，系统正在处理中，请稍等。")
    elif return_time > 30 * 60:
        print("您的订单已经提交，预计等待时间超过30分钟，请耐心等待。")
    else:
        print("您的订单已经提交，最新预估等待时间" + show_time + "，请耐心等待。")

# 跳转-单程
def finishMethod(tourFlag, time, returnObj, params=None):
    if time == -1:
        action_url = "https://kyfw.12306.cn/otn/"
        if tourFlag == 'dc':
            # 异步下单-单程
            action_url += "confirmPassenger/resultOrderForDcQueue"
        elif tourFlag == 'wc':
            # 异步下单-往程
            action_url += "confirmPassenger/resultOrderForWcQueue"
        elif tourFlag == 'fc':
            # 异步下单-返程
            action_url += "confirmPassenger/resultOrderForFcQueue"
        elif tourFlag == 'gc':
            # 异步下单-改签
            action_url += "confirmPassenger/resultOrderForGcQueue"
        orderId = returnObj['orderId'] if 'orderId' in returnObj else ''
        #ht.post(url=action_url, params=params)
        # 处理订单提交成功操作
        print('车票预定成功订单号为：%s，请立即打开浏览器登录12306，访问‘未完成订单’在45分钟内完成支付！' % orderId)
        pass
    else:
        procFail(time, returnObj)

# 订单提交失败
def procFail(flag, returnObj):
    renewURL = "<a href='https://kyfw.12306.cn/otn/initNoComplete'>[重新购票]</a>"
    my12306URL = "<a href='https://kyfw.12306.cn/otn/index/initMy12306'>[我的12306]</a>"
    if flag == -1:
        return
    elif flag == -2:
        if returnObj['errorcode'] == 0:
            print("占座失败，原因:" + returnObj['msg'] + " 请访问" + my12306URL + ",办理其他业务.")
        else:
            print("占座失败，原因:" + returnObj['msg'] + " 请访问" + renewURL + ",重新选择其它车次.")
    elif flag == -3:
        print("订单已撤销 请访问" + renewURL + ",重新选择其它车次.")
    else:
        # 进入未完成订单页面
        # url = "https://dynamic.12306.cn/otsweb/order/myOrderAction.do?method=queryMyOrderNotComplete&leftmenu=Y&fakeParent=true";
        pass


def main():
    f = open("./resources/order/confirm_passenger_init.html", 'r', encoding="utf-8")
    submitResult = f.read()
    f.close()

    parser = ParserConfirmPassengerInitPage()
    parser.feed(submitResult)

    f = open('hend_params.txt', 'w')
    f.write(str((parser.get_hidden_params()).items()))
    f.close()


if __name__ == '__main__':
    main()
