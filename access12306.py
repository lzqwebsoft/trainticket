# coding: utf8
import time
import tkinter
import ui.LoginUI, ui.OrderConfirmUI, ui.QueryTrainUI
from core import login,order,query
from common.httpaccess import HttpTester


class AccessTrainOrderNetWork:
    def __init__(self):
        self.ht = HttpTester()
        self.ht.addCookiejar()

        # 获取用户帐号信息
        self.userInfo = login.getUserInfo()
        # 装载列车站台编码
        self.allStationCodes = {}

        # 登录验证令牌
        self.login_rand = ''

        self.randImage = None
        self.queryFrame = None
        self.comfirmFrame = None
        # 记录当前查询的参数值
        self.currentSelectedParams = {}
        # 记录车票预订的HTML解析对象
        self.parser = None

        # 车票预定时所填的参数数组
        self.orderParams = None

    def access(self):
        if self.userInfo:
            login_result = login.getRandImageUrlAndCodeRand(self.ht)
            rand_image_url = login_result.get('url', '')
            self.login_rand = login_result.get('rand', '')
            if rand_image_url:
                self.randImage = ui.LoginUI.LoginFrame(rand_image_url)
                self.randImage.loginButton.configure(command=self.processLoginCallBack)
                self.randImage.randCode.bind("<Return>", self.processLoginCallBack)
                self.randImage.show()

    # 处理登录回调
    def processLoginCallBack(self, event=None):
        if self.randImage:
            # 获取前台用户输入的输入证码
            randCode = self.randImage.randCode.get()
            if randCode:
                loginResult = login.login(ht=self.ht, username=self.userInfo[0], password=self.userInfo[1],
                                          randCode=randCode, rand=self.login_rand)
                if loginResult:
                    # 登录成功，关闭登框
                    self.randImage.quit()
                    # 更新城市编码表
                    query.updateCityCode(self.ht)
                    # 装载列车站点编码
                    self.allStationCodes = query.getAllStationCodes()
                    # 获取默认的列车查询信息
                    defaultQueryParams = query.getDefaultQueryParams()
                    # 启动列车查询窗体
                    self.queryFrame = ui.QueryTrainUI.QueryTrainFrame(initQueryParams=defaultQueryParams)
                    self.queryFrame.selectButton.configure(command=self.queryTrainsCallBack)
                    self.queryFrame.show()
                else:
                    print("登录失败，请再来一次")
                    self.randImage.refreshImg()
                    self.randImage.randCode.delete(0, tkinter.END)
            else:
                print("请输入验证码")

    # 处理查询回调
    def queryTrainsCallBack(self):
        if not self.queryFrame:
            return
        from_station = self.queryFrame.fromStation.get()
        to_station = self.queryFrame.toStation.get()
        train_date = self.queryFrame.trainDate.get()
        start_time = self.queryFrame.getSelectedTrainTime()
        end_time = self.queryFrame.endTime.get()
        trainClass = self.queryFrame.getSelectedTrainClass()
        trainPassType = self.queryFrame.getChoiceTrainPassType()
        trainNos = self.queryFrame.trainNo.get()
        # 当时间未填时，设置为当前时间
        if not train_date or train_date.strip() == '': train_date = time.strftime("%Y-%m-%d", time.localtime())
        # 记录当前的查询条件
        self.currentSelectedParams = {
            'from_station': self.allStationCodes.get(from_station, ''),
            'to_station': self.allStationCodes.get(to_station, ''),
            'train_date': train_date,
            'start_time': start_time,
            'end_time': end_time,
            'trainNos': trainNos,
            'trainClass': trainClass,
            'trainPassType': trainPassType,
            'justShowCanBuy': self.queryFrame.showCanBuySwitch.get()
        }

        isAutoQuery = self.queryFrame.autoQuerySwitch.get()     # 自动查询开关设置的值
        # 执行查询，得到所有满足条件的列车
        trains = query.queryTrains(self.ht, query_params=self.currentSelectedParams)
        self.queryFrame.infoStartDateLabel.configure(
            text="出发日期：%s %s->%s(共 %s 趟列车)" % (train_date, from_station, to_station, len(trains)))
        if trains:
            print("%s 查询成功!" % time.strftime('%H:%M:%S', time.localtime(time.time())))
        self.queryFrame.resultTable.updateResult(trainDatas=trains, orderHandleFuc=self.orderTrainsCallBack)
        # 判断查询的结果，如果没有可预订的列车，且开启了自动查询，则进行自动查询循环
        canWebBuy = False
        for train in trains:
            tmp = train.get('canWebBuy', 'N')
            if tmp == 'Y':
                canWebBuy = True
                break
        if isAutoQuery and not canWebBuy:
            self.queryFrame.selectButton.configure(state=tkinter.DISABLED, text='自动查询中')
            print('自动查询开启，5秒后进行下一波查询.')
            self.queryFrame.root.after(5000, self.queryTrainsCallBack)
        else:
            self.queryFrame.selectButton.configure(state=tkinter.NORMAL, text='查询')

    # 处理列车预定按钮回调
    def orderTrainsCallBack(self, selectStr='', row=0):
        if selectStr:
            from_station = self.queryFrame.fromStation.get()
            # 提交预定，获取初始化乘客确认页面内容
            submitResult = order.submitOrderRequest(self.ht, selectStr, queryParams=self.currentSelectedParams)
            if submitResult:
                self.parser = order.ParserConfirmPassengerInitPage(submitResult)
                self.parser.feed(submitResult)
                # 得到联系人
                contacts = order.getAllContacts(self.ht)
                # 列车信息
                trainInfo = self.parser.get_train_info()
                # 验证码地址
                img_rand_code_url = self.parser.get_img_code_url()
                # 订单选座参数
                passenger_params = self.parser.get_ticketInfoForPassengerForm()
                # 判断得到的数据是否合法
                if img_rand_code_url and trainInfo and contacts and passenger_params:
                    # self.queryFrame.quit()      # 注销查询窗体
                    # self.queryFrame = None
                    self.comfirmFrame = ui.OrderConfirmUI.ConfirmPassengerFrame(contacts=contacts,
                                                                             rand_image_url=img_rand_code_url,
                                                                             train_info=trainInfo,
                                                                             passenger_params=passenger_params)
                    self.comfirmFrame.backButton.configure(command=self.backToTrainQueryCallBack)
                    self.comfirmFrame.submitButton.configure(command=self.submitOrderCallBack)
                    self.comfirmFrame.show()
                else:
                    print('解析车票预订画面失败,详情查看当前目录下的submitResult.html文件.')
            else:
                print('预订画面获取失败!')
        else:
            print('非法的请求selectStr为空：%s' % selectStr)

    # 处理车票预定窗体的重新选择回调
    def backToTrainQueryCallBack(self):
        # 注销车票预订窗体
        self.comfirmFrame.quit()
        self.comfirmFrame = None
        # 新建查询窗体
        #self.queryFrame = ui.QueryTrainUI.QueryTrainFrame(initQueryParams=self.currentSelectedParams)
        #self.queryFrame.selectButton.configure(command=self.queryTrainsCallBack)
        #self.queryFrame.show()

    # 订单提交回调
    def submitOrderCallBack(self):
        # 整合POST上传参数
        # hidden_params = self.parser.get_hidden_params()
        passenger_info = self.comfirmFrame.getAllPassengerParams()
        count = self.comfirmFrame.getCustomerCount()

        # 订单提交页面隐藏参数
        order_request_params = self.parser.get_order_request_params()
        ticketInfoForPassengerForm = self.parser.get_ticketInfoForPassengerForm()

        passengerTicketStr = ''
        oldPassengersStr = ''
        oldPassengers = []
        passengerTickets = []
        for i in range(count):
            passengerTickets.append(passenger_info['passenger_' + str(i + 1) + '_seat'] + ",0," + passenger_info[
                'passenger_' + str(i + 1) + '_ticket'] + "," + passenger_info[
                                        'passenger_' + str(i + 1) + '_name'] + "," + passenger_info[
                                        'passenger_' + str(i + 1) + '_cardtype'] + "," + passenger_info[
                                        'passenger_' + str(i + 1) + '_cardno'] + "," + passenger_info[
                                        'passenger_' + str(i + 1) + '_mobileno'] + ",Y")
            # 这里最后一位暂时全部设定为成年人
            # adult: "1",
            # child: "2",
            # student: "3",
            # disability: "4"
            oldPassengers.append(passenger_info['passenger_' + str(i + 1) + '_name'] + "," + passenger_info[
                'passenger_' + str(i + 1) + '_cardtype'] + "," + passenger_info[
                                     'passenger_' + str(i + 1) + '_cardno'] + "," + '1')

        passengerTicketStr = "_".join(passengerTickets)
        oldPassengersStr = "_".join(oldPassengers) + "_"
        image_code = self.comfirmFrame.getRandCode()
        image_code_rand = self.parser.get_img_code_rand()
        # ===================DEBUG=================
        # f = open('post_params.txt', 'w')
        # f.write(str(self.orderParams))
        # f.close()
        # =========================================
        # 检查用户输入验证码的合法性
        checkResult = order.checkOrderImgCode(self.ht, rand=image_code_rand, img_code=image_code,
                                              token=self.parser.globalRepeatSubmitToken)
        if checkResult:
            # 检证用户提交的乘客信息的合法性
            checkResult = order.checkOrderInfo(self.ht, randCode=image_code, passengerTicketStr=passengerTicketStr,
                                               oldPassengersStr=oldPassengersStr, tour_flag='dc',
                                               token=self.parser.globalRepeatSubmitToken)
            if checkResult:
                # 参数合法，则显示车票预定对话框
                # 排队提示对话框
                seat_type = passenger_info['passenger_1_seat']
                queueCounParams = [
                    ('train_date', str(time.ctime(order_request_params['train_date']['time'] / 1000))),
                    ('train_no', order_request_params['train_no']),
                    ('stationTrainCode', order_request_params['station_train_code']),
                    ('seatType', seat_type),
                    ('fromStationTelecode', order_request_params['from_station_telecode']),
                    ('toStationTelecode', order_request_params['to_station_telecode']),
                    ('leftTicket', ticketInfoForPassengerForm['queryLeftTicketRequestDTO']['ypInfoDetail']),
                    ('purpose_codes', 'ADULT'),
                    ('isCheckOrderInfo', checkResult['isCheckOrderInfo']),
                    ('REPEAT_SUBMIT_TOKEN', self.parser.globalRepeatSubmitToken)
                ]
                # 订单提交自动出票参数
                self.orderParams = [
                    ('passengerTicketStr', passengerTicketStr),
                    ('oldPassengerStr', oldPassengersStr),
                    ('randCode', image_code),
                    ('purpose_codes', ticketInfoForPassengerForm['purpose_codes']),
                    ('key_check_isChange', ticketInfoForPassengerForm['key_check_isChange']),
                    ('leftTicketStr', ticketInfoForPassengerForm['leftTicketStr']),
                    ('train_location', ticketInfoForPassengerForm['train_location']),
                    ('REPEAT_SUBMIT_TOKEN', self.parser.globalRepeatSubmitToken)
                ]
                queue_note = order.getQueueCount(self.ht, queueCounParams, seat_type)
                ui.OrderConfirmUI.ConfirmOrderDialog(self.comfirmFrame.root, queue_note, self.parser.get_train_info(),
                                                  self.comfirmFrame.getPassengerInfo(), self.comfirmOrderSubmitCallBack)

    # 用户点击提交订单确认对话框的确认按钮时回调
    def comfirmOrderSubmitCallBack(self):
        # 检查单程预定允许排队
        checkResult = order.checkQueueOrder(self.ht, 'dc', self.orderParams)
        if checkResult:
            # 开始排队
            timer = order.OrderQueueWaitTime(self.ht, 'dc', order.waitFunc, order.finishMethod)
            timer.start()


def main():
    temp = AccessTrainOrderNetWork()
    temp.access()


if __name__ == "__main__":
    main()