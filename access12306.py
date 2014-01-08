# coding: utf8
import time
from ui import *
from core import *
from common.httpaccess import HttpTester
from tkinter import *


class AccessTrainOrderNetWork:
    def __init__(self):
        self.ht = HttpTester()
        self.ht.addCookiejar()

        self.userInfo = login.getUserInfo()

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
            randImageUrl = login.getRandImageUrl(self.ht)
            if randImageUrl:
                self.randImage = LoginUI.LoginFrame(randImageUrl)
                self.randImage.loginButton.configure(command=self.processLoginCallBack)
                self.randImage.randCode.bind("<Return>", self.processLoginCallBack)
                self.randImage.show()

    # 处理登录回调
    def processLoginCallBack(self, event=None):
        if self.randImage:
            randCode = self.randImage.randCode.get()
            if randCode.strip() != '':
                loginResult = login.login(ht=self.ht, username=self.userInfo[0], password=self.userInfo[1],
                                          randcode=randCode)
                if loginResult:
                    # 登录成功，关闭登框
                    self.randImage.quit()
                    # 更新城市编码表
                    query.updateCityCode(self.ht)
                    # 启动列车查询窗体
                    self.queryFrame = QueryTrainUI.QueryTrainFrame()
                    self.queryFrame.selectButton.configure(command=self.queryTrainsCallBack)
                    self.queryFrame.show()
                else:
                    print("登录失败，请再来一次")
                    self.randImage.refreshImg()
                    self.randImage.randCode.delete(0, END)
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
        trainClass = self.queryFrame.getSelectedTrainClass()
        trainPassType = self.queryFrame.getChoiceTrainPassType()
        # 当时间未填时，设置为当前时间
        if not train_date or train_date.strip() == '': train_date = time.strftime("%Y-%m-%d", time.localtime())
        # 记录当前的查询条件
        self.currentSelectedParams['from_station'] = from_station
        self.currentSelectedParams['to_station'] = to_station
        self.currentSelectedParams['train_date'] = train_date
        self.currentSelectedParams['start_time'] = start_time
        self.currentSelectedParams['trainClass'] = trainClass
        self.currentSelectedParams['trainPassType'] = trainPassType
        # 执行查询，得到所有满足条件的列车
        trains = query.queryTrains(self.ht, from_station=from_station, to_station=to_station,
                                   train_date=train_date, start_time=start_time, trainClass=trainClass,
                                   trainPassType=trainPassType)
        self.queryFrame.infoStartDateLabel.configure(
            text="出发日期：%s %s->%s(共 %s 趟列车)" % (train_date, from_station, to_station, str(len(trains))))
        if len(trains) > 0:
            print("%s 查询成功!" % time.strftime('%H:%M:%S', time.localtime(time.time())))
        self.queryFrame.resultTable.updateResult(trainDatas=trains, orderHandleFuc=self.orderTrainsCallBack)

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
                # 订单选坐参数
                passenger_params = self.parser.get_ticketInfoForPassengerForm()

                # 席别信息
                # seats_info = self.parser.get_current_seats()
                # 席别下拉框
                # seats_types = self.parser.get_seats_types()
                # 票种类型
                # ticket_types = self.parser.get_ticket_types()
                # 证件类型
                # card_types = self.parser.get_card_types()
                # 判断得到的数据是否合法
                if img_rand_code_url and trainInfo and contacts and passenger_params:
                    self.queryFrame.quit()      # 注销查询窗体
                    self.queryFrame = None
                    self.comfirmFrame = OrderConfirmUI.ConfirmPassengerFrame(contacts=contacts,
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
        self.queryFrame = QueryTrainUI.QueryTrainFrame()
        self.queryFrame.selectButton.configure(command=self.queryTrainsCallBack)
        self.queryFrame.show()

    # 订单提交回调
    def submitOrderCallBack(self):
        # 整合POST上传参数
        hidden_params = self.parser.get_hidden_params()
        passenger_info = self.comfirmFrame.getAllPassengerParams()
        count = self.comfirmFrame.getCustomerCount()
        self.orderParams = []
        for i in range(count):
            if i == 0:
                hidden_params['orderRequest.reserve_flag'] = 'A'
                hidden_params['oldPassengers'] = passenger_info['passenger_1_name'] + "," + passenger_info[
                    'passenger_1_cardtype'] + "," + passenger_info['passenger_1_cardno']
                hidden_params['passengerTickets'] = passenger_info['passenger_1_seat'] + ",0," + passenger_info[
                    'passenger_1_ticket'] + "," + passenger_info['passenger_1_name'] + "," + passenger_info[
                                                        'passenger_1_cardtype'] + "," + passenger_info[
                                                        'passenger_1_cardno'] + "," + passenger_info[
                                                        'passenger_1_mobileno'] + ",Y"
                self.orderParams = list(hidden_params.items())
                self.orderParams.extend(list(passenger_info.items()))
            else:
                oldPassengers = passenger_info['passenger_' + str(i + 1) + '_name'] + "," + passenger_info[
                    'passenger_' + str(i + 1) + '_cardtype'] + "," + passenger_info[
                                    'passenger_' + str(i + 1) + '_cardno']
                passengerTickets = passenger_info['passenger_' + str(i + 1) + '_seat'] + ",0," + passenger_info[
                    'passenger_' + str(i + 1) + '_ticket'] + "," + passenger_info[
                                       'passenger_' + str(i + 1) + '_name'] + "," + passenger_info[
                                       'passenger_' + str(i + 1) + '_cardtype'] + "," + passenger_info[
                                       'passenger_' + str(i + 1) + '_cardno'] + "," + passenger_info[
                                       'passenger_' + str(i + 1) + '_mobileno'] + ",Y"
                self.orderParams.append(('oldPassengers', oldPassengers))
                self.orderParams.append(('passengerTickets', passengerTickets))
        rand = self.comfirmFrame.getRandCode()
        # ===================DEBUG=================
        # f = open('post_params.txt', 'w')
        # f.write(str(self.orderParams))
        # f.close()
        # =========================================
        # 检查参数的合法性
        checkResult = order.checkOrderInfo(self.ht, params=self.orderParams, rand=rand)
        if checkResult:
            # 参数合法，则显示车票预定对话框
            # 排队提示对话框
            seat_type = passenger_info['passenger_1_seat']
            queueCounParams = [
                ('train_date', hidden_params['orderRequest.train_date']),
                ('train_no', hidden_params['orderRequest.train_no']),
                ('station', hidden_params['orderRequest.station_train_code']),
                ('seat', seat_type),
                ('from', hidden_params['orderRequest.from_station_telecode']),
                ('to', hidden_params['orderRequest.to_station_telecode']),
                ('ticket', hidden_params['leftTicketStr'])]
            queue_note = order.getQueueCount(self.ht, queueCounParams, seat_type)
            OrderConfirmUI.ConfirmOrderDialog(self.comfirmFrame.root, queue_note, self.parser.get_train_info(),
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