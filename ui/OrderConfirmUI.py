# coding: utf8
import json
import io
import random
import socket
import urllib.error

try:
    # Python2
    from Tkinter import *
    from ttk import *
    from urllib2 import urlopen
    #import tkMessageBox as messagebox
except ImportError:
    # Python3
    from tkinter import *
    from tkinter.ttk import *
    from urllib.request import urlopen
    #from tkinter import messagebox
from PIL import Image, ImageTk


class ConfirmPassengerFrame:
    def __init__(self, contacts=None, rand_image_url='', train_info=None, passenger_params=None,
                 ticket_types=None, card_types=None):
        self.root = Toplevel()
        self.root.title("车票预订")
        self.root['padx'] = 20
        self.root['pady'] = 10

        # 列车信息
        trainInfoPanel = Frame(self.root)
        trainInfoPanel.pack(fill=X, pady=8)

        trainInfoTitle = Label(trainInfoPanel, text="列车信息", font=('黑体', 12, 'bold'),
                               foreground='white', background="#8DB7E0")
        trainInfoTitle.grid(row=0, column=0, columnspan=5, sticky=W + E + N + S)
        if train_info and len(train_info) > 0:
            for x in range(len(train_info)):
                label = Label(trainInfoPanel, text=train_info[x], foreground='#2C72BA', background='#F3F8FC', width=20)
                label.grid(row=1, column=x, padx=1, sticky=W + E + N + S)
        else:
            label = Label(trainInfoPanel, text='列车信息获取失败(〒_〒)!', foreground='red', width=20)
            label.grid(row=1, column=0, padx=1, sticky=W + E + N + S)

        row = 1
        if 'leftDetails' in passenger_params and passenger_params['leftDetails']:
            seats_info = passenger_params['leftDetails']
            column = 0
            for text in seats_info:
                if column % 5 == 0:
                    row += 1
                    column = 0
                seatLabel = Label(trainInfoPanel, text=text, width=20)
                seatLabel.grid(row=row, column=column, padx=1, sticky=W + E + N + S)
                column += 1
        else:
            row = row + 1
            label = Label(trainInfoPanel, text='席别信息获取失败(〒_〒)!', foreground='red', width=20)
            label.grid(row=row, column=0, padx=1, sticky=W + E + N + S)

        promptLabel = Label(trainInfoPanel, text="以上余票信息随时发生变化，仅作参考", foreground='red')
        promptLabel.grid(row=row + 1, column=0, columnspan=5, sticky=W + E + N + S)

        # 我的常用联系人
        contactPanel = Frame(self.root)
        contactPanel.pack(fill=X, pady=8)
        contactTitle = Label(contactPanel, text="常用联系人", font=('黑体', 12, 'bold'),
                             foreground='white', background="#8DB7E0")
        contactTitle.grid(row=0, column=0, columnspan=8, sticky=W + E + N + S)
        self.contacts = contacts
        self.users = []
        if self.contacts and len(self.contacts) > 0:
            row = 0
            column = 0
            for user in self.contacts:
                var = IntVar()
                if column % 8 == 0:
                    row += 1
                    column = 0
                chk = Checkbutton(contactPanel, text=user['passenger_name'], variable=var, width=9)
                chk.bind("<Button-1>", self.contactChangeCallBack)
                chk.grid(row=row, column=column, sticky=W + E + N + S, padx=2)
                self.users.append(var)
                column += 1
        else:
            label = Label(contactPanel, text='未查找到常用联系人')
            label.grid(row=1, column=1, sticky=W + E + N + S)
            contactPanel.columnconfigure(0, weight=1)
            contactPanel.columnconfigure(2, weight=1)

        # 乘车人信息
        customerPanel = Frame(self.root)
        customerPanel.pack(fill=X, pady=8)
        customerTitle = Label(customerPanel, text="乘车人信息", font=('黑体', 12, 'bold'),
                              foreground='white', background="#8DB7E0")
        customerTitle.pack(fill=X)

        self.allCustomerFileds = []
        self.seats_types = {}
        self.ticket_types = {}
        self.card_types = {}
        # 乘客输入框数据
        if 'limitBuySeatTicketDTO' in passenger_params and 'seat_type_codes' in passenger_params[
            'limitBuySeatTicketDTO']:
            self.seats_types = {seat_type_codes['id']: seat_type_codes['value'] for seat_type_codes in
                                passenger_params['limitBuySeatTicketDTO']['seat_type_codes']}
            self.ticket_types = {ticket_type_codes['id']: ticket_type_codes['value'] for ticket_type_codes in
                                 passenger_params['limitBuySeatTicketDTO']['ticket_type_codes']}
            self.card_types = {cardTypes['id']: cardTypes['value'] for cardTypes in passenger_params['cardTypes']}

        self.customerTable = Frame(customerPanel)
        self.customerTable.pack(fill=X)
        customerInfoHead = CustomerInfoHead(self.customerTable)
        customerInfoHead.pack(fill=X)
        customerInfoContent = CustomerInfoContent(self.customerTable, seats_types=self.seats_types,
                                                  ticket_types=self.ticket_types, card_types=self.card_types)
        customerInfoContent.deleteOparetorLabel.bind("<Button-1>", self.removeCurstomerCallBack)
        customerInfoContent.pack(fill=X, pady=5)
        self.allCustomerFileds.append(customerInfoContent)

        customerOparetorPanel = Frame(customerPanel)
        customerOparetorPanel.pack(fill=X)
        randImageLable = Label(customerOparetorPanel, text="*请输入验证码:")
        randImageLable.grid(row=0, column=0, padx=5, pady=5)
        self.randImage = Entry(customerOparetorPanel, width=10)
        self.randImage.grid(row=0, column=1, padx=5, pady=5)

        self.rand_image_url = rand_image_url
        if rand_image_url and rand_image_url.strip():
            while True:
                try:
                    image_bytes = urlopen(self.rand_image_url).read()
                    break
                except socket.timeout:
                    print('获取验证码超时：%s\r\n重新获取.' % (self.rand_image_url))
                    continue
                except urllib.error.URLError as e:
                    if isinstance(e.reason, socket.timeout):
                        print('获取验证码超时：%s\r\n重新获取.' % (self.rand_image_url))
                        continue
            data_stream = io.BytesIO(image_bytes)
            pil_image = Image.open(data_stream)
            self.tk_image = ImageTk.PhotoImage(pil_image)
            self.randImageShow = Label(customerOparetorPanel, image=self.tk_image, background='brown')
            self.randImageShow.grid(row=0, column=3, padx=5, pady=5)
            refreshImage = Button(customerOparetorPanel, text='刷新验证码', command=self.refreshImageCallBack)
            refreshImage.grid(row=0, column=4, padx=5, pady=5)
        else:
            print("验证码URL不能为空")

        self.addCoustomerButton = Button(customerOparetorPanel, text="添加1位乘车人", command=self.addOneCustomerCallBack)
        self.addCoustomerButton.grid(row=0, column=6, padx=5, pady=5)

        customerOparetorPanel.columnconfigure(5, weight=1)

        # 按钮操作区
        operatorPanel = Frame(self.root)
        operatorPanel.pack(fill=X, pady=8)
        self.backButton = Button(operatorPanel, text="关闭")
        self.backButton.grid(row=0, column=1, sticky=W + E + N + S, padx=5)
        self.submitButton = Button(operatorPanel, text="提交订单")
        self.submitButton.grid(row=0, column=2, sticky=W + E + N + S, padx=5)
        operatorPanel.columnconfigure(0, weight=1)
        operatorPanel.columnconfigure(3, weight=1)

    def show(self):
        width = 750
        height = 500
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = int((ws / 2) - (width / 2))
        y = int((hs / 2) - (height / 2))
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        self.root.resizable(False, True)
        self.root.mainloop()

    # 由乘客输入列中获取乘客信息值
    def getAllPassengerParams(self):
        passenger_fields = self.allCustomerFileds
        params = {}
        if passenger_fields and len(passenger_fields) > 0:
            for field in passenger_fields:
                param = field.getSetCustomerInfo()
                params.update(param)
        return params

    # 由乘客输入列中获取乘客信息文本
    def getPassengerInfo(self):
        passenger_fields = self.allCustomerFileds
        infos = []
        if passenger_fields and len(passenger_fields) > 0:
            for field in passenger_fields:
                infos.append(field.getSetCusomerInfoText())
        return infos

    # 获取输入的输入的验证码
    def getRandCode(self):
        rand_code = self.randImage.get()
        if rand_code.strip() != "":
            rand_code = rand_code.strip()
        return rand_code

    # 返回设置的乘客个数
    def getCustomerCount(self):
        return len(self.allCustomerFileds)

    def refreshImageCallBack(self):
        if self.rand_image_url and self.rand_image_url.strip() != '':
            url = self.rand_image_url + "&" + str(random.random())
            while True:
                try:
                    image_bytes = urlopen(url).read()
                    break
                except socket.timeout:
                    print('获取验证码超时：%s\r\n重新获取.' % (self.rand_image_url))
                    continue
                except urllib.error.URLError as e:
                    if isinstance(e.reason, socket.timeout):
                        print('获取验证码超时：%s\r\n重新获取.' % (self.rand_image_url))
                        continue
            data_stream = io.BytesIO(image_bytes)
            pil_image = Image.open(data_stream)
            self.tk_image = ImageTk.PhotoImage(pil_image)
            self.randImageShow.configure(image=self.tk_image)
        else:
            print("验证码URL不能为空")

    # 选中联系人复选框时触发
    def contactChangeCallBack(self, event):
        widget = event.widget
        selected = not 'selected' in widget.state()
        username = widget.config('text')[-1].strip()
        count = len(self.allCustomerFileds)
        if selected and count >= 5:
            print("乘客一次不能超过5人")
            return
        contained = False
        parent_name = ''
        for customerFiled in self.allCustomerFileds:
            if customerFiled.getCustomerName() == username:
                contained = True
                parent_name = str(customerFiled)

        if not selected and contained:
            if count == 1:
                self.allCustomerFileds[0].clearCustomerInfo()
            else:
                # 去掉己添加的用户
                self.removeCustomer(parent_name=parent_name)
        elif selected and not contained:
            # 当乘车人域中有一个输入域为空白，则将其设置为选中联系人，不用新建输入域
            emptyField = None
            for customerFiled in self.allCustomerFileds:
                if customerFiled.getCustomerName().strip() == "":
                    emptyField = customerFiled
                    break
                    # 从当前联系人列表中检索该联系人信息
            current_user_info = None
            for contact in self.contacts:
                passenger_name = contact['passenger_name'].strip()
                if passenger_name == username:
                    current_user_info = contact
                    break
            if emptyField != None:
                customerFiled.setCustomerInfo(current_user_info)
            else:
                if count == 4:
                    self.addCoustomerButton.configure(state=DISABLED)
                    # 添加选中的用户
                self.addNoneCustomer(index=count + 1, user_info=current_user_info)

    # 添加1位新的乘客时添加
    def addOneCustomerCallBack(self):
        count = len(self.allCustomerFileds)
        if count > 5:
            return
        if count == 4:
            self.addCoustomerButton.configure(state=DISABLED)
        self.addNoneCustomer(index=count + 1)

    # 删除联系人时添加
    def removeCurstomerCallBack(self, event):
        if len(self.allCustomerFileds) == 1:
            # messagebox.showerror("错误", "最后一位乘客不能删除！")
            self.allCustomerFileds[0].clearCustomerInfo()
            return
        widget = event.widget
        parent_name = widget.winfo_parent()   # 得到父组件名
        #parentWidget =widget.nametowidget(parent_name) # 由父组件名得到父组件
        #parentWidget.pack_forget()            # 界面中删除父组件
        #self.allCustomerFileds.remove(parentWidget)

        self.removeCustomer(parent_name=parent_name)

    def addNoneCustomer(self, index=1, user_info=None):
        newCustomerInfoContent = CustomerInfoContent(self.customerTable, index=index, seats_types=self.seats_types,
                                                     ticket_types=self.ticket_types, card_types=self.card_types)
        newCustomerInfoContent.pack(fill=X, pady=5)
        newCustomerInfoContent.deleteOparetorLabel.bind("<Button>", self.removeCurstomerCallBack)
        newCustomerInfoContent.setCustomerInfo(user_info)    # 设置乘客信息
        self.allCustomerFileds.append(newCustomerInfoContent)

    def removeCustomer(self, parent_name=None):
        index = 1
        parentWidget = None
        for customerFiled in self.allCustomerFileds:
            if str(customerFiled) == parent_name:
                customerFiled.pack_forget()
                parentWidget = customerFiled
                continue
            customerFiled.udpateNoLabelText(index)  # 更新乘业客的索引
            index += 1
        if parentWidget: self.allCustomerFileds.remove(parentWidget)
        # 如果乘客数小于5，则显示添加按钮
        if len(self.allCustomerFileds) < 5:
            self.addCoustomerButton.configure(state=NORMAL)

    def quit(self):
        self.root.destroy()


class CustomerInfoHead(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)

        label = Label(self, width=5)
        label.grid(row=0, column=0, padx=5)

        label = Label(self, text="席别", width=8)
        label.grid(row=0, column=1, padx=5)

        label = Label(self, text="票种", width=9)
        label.grid(row=0, column=2, padx=5)

        label = Label(self, text="姓名", width=10)
        label.grid(row=0, column=3, padx=5)

        label = Label(self, text="证件类型", width=13)
        label.grid(row=0, column=4, padx=5)

        label = Label(self, text="证件号码", width=22)
        label.grid(row=0, column=5, padx=5)

        label = Label(self, text="手机号", width=12)
        label.grid(row=0, column=6, padx=5)

        label = Label(self, text="操作", width=4)
        label.grid(row=0, column=7, padx=5)


class CustomerInfoContent(Frame):
    def __init__(self, parent, index=1, seats_types=None, ticket_types=None, card_types=None):
        Frame.__init__(self, parent)

        self.index = index
        self.noLabel = Label(self, text="第%d位" % index)
        self.noLabel.grid(row=0, column=0, padx=5)

        self.seats_types = seats_types
        seats_texts = list(self.seats_types.values())
        self.seatTypeListBox = Combobox(self, values=seats_texts, state="readonly", width=6)
        self.seatTypeListBox.set(seats_texts[0])
        self.seatTypeListBox.grid(row=0, column=1, padx=5)

        self.ticket_types = ticket_types
        ticket_type_texts = list(self.ticket_types.values())
        self.customerTypeListBox = Combobox(self, values=ticket_type_texts, state="readonly", width=6)
        self.customerTypeListBox.set(ticket_type_texts[0])
        self.customerTypeListBox.grid(row=0, column=2, padx=5)

        self.customerName = Entry(self, width=10)
        self.customerName.grid(row=0, column=3, padx=5)

        self.card_types = card_types
        card_type_texts = list(self.card_types.values())
        self.cardTypeListBox = Combobox(self, values=card_type_texts, state="readonly", width=10)
        self.cardTypeListBox.set(card_type_texts[0])
        self.cardTypeListBox.grid(row=0, column=4, padx=5)

        self.cardNo = Entry(self, width=22)
        self.cardNo.grid(row=0, column=5, padx=5)

        self.cellphone = Entry(self, width=12)
        self.cellphone.grid(row=0, column=6, padx=5)

        self.deleteOparetorLabel = Label(self, text="删除", width=4, font=('黑体', 11, 'underline'), foreground='blue')
        self.deleteOparetorLabel.grid(row=0, column=7, padx=5)

    def udpateNoLabelText(self, index):
        self.index = index
        self.noLabel.configure(text="第%d位" % index)

    def getCustomerName(self):
        name = self.customerName.get()
        if name != None:
            name = name.strip()
        return name

    def setCustomerName(self, customerName=''):
        self.customerName.delete(0, END)
        if customerName.strip() != '':
            customerName = customerName.strip()
            self.customerName.insert(0, customerName)

    def setCustomerInfo(self, user_info=None):
        if not user_info:
            return
            # 由用户信息设置票类
        ticket_type = self.ticket_types[user_info['passenger_type']]
        self.customerTypeListBox.set(ticket_type)
        # 由用户信息设置用户名
        self.setCustomerName(user_info['passenger_name'])
        # 由用户信息设置证件类
        card_type = self.card_types[user_info['passenger_id_type_code']]
        self.cardTypeListBox.set(card_type)
        # 用用户信息设置证件编号
        self.cardNo.delete(0, END)
        self.cardNo.insert(0, user_info['passenger_id_no'])
        # 由用户信息设置手机号
        self.cellphone.delete(0, END)
        self.cellphone.insert(0, user_info['mobile_no'])

    def clearCustomerInfo(self):
        # 清空票类
        ticket_type = list(self.ticket_types.values())
        self.customerTypeListBox.set(ticket_type[0])
        # 清空用户名
        self.setCustomerName('')
        # 清空证件类
        card_type = list(self.card_types.values())
        self.cardTypeListBox.set(card_type[0])
        # 清空证件编号
        self.cardNo.delete(0, END)
        # 清空手机号
        self.cellphone.delete(0, END)

    # 获取页面中设定的乘客信息值
    def getSetCustomerInfo(self):
        params = {}
        # 得到设置的席别
        params['passenger_%d_seat' % self.index] = ''
        seat_type = self.seatTypeListBox.get()
        seat_type = seat_type.strip()
        for value, text in self.seats_types.items():
            if text == seat_type:
                params['passenger_%d_seat' % self.index] = value
                break
            # 得到选中的票类
        params['passenger_%d_ticket' % self.index] = ''
        ticket_type = self.customerTypeListBox.get()
        ticket_type = ticket_type.strip()
        for value, text in self.ticket_types.items():
            if ticket_type == text:
                params['passenger_%d_ticket' % self.index] = value
                break
            # 得到设置的用户名
        params['passenger_%d_name' % self.index] = self.getCustomerName()
        # 得到证件类型
        params['passenger_%d_cardtype' % self.index] = ''
        card_type = self.cardTypeListBox.get()
        card_type = card_type.strip()
        for value, text in self.card_types.items():
            if card_type == text:
                params['passenger_%d_cardtype' % self.index] = value
                break
            # 得到证件号
        params['passenger_%d_cardno' % self.index] = self.cardNo.get()
        # 手机号
        params['passenger_%d_mobileno' % self.index] = self.cellphone.get()

        return params

    # 获取窗体中设定的乘客信息文本
    # 按席别，票种，姓名，证件类型，证件号，手机号的顺序排序
    def getSetCusomerInfoText(self):
        set_values = []
        # 得到设置的席别
        seat_type = self.seatTypeListBox.get()
        seat_type = seat_type.strip()
        set_values.append(seat_type)
        # 得到选中的票类
        ticket_type = self.customerTypeListBox.get()
        ticket_type = ticket_type.strip()
        set_values.append(ticket_type)
        # 得到设置的用户名
        set_values.append(self.getCustomerName())
        # 得到证件类型
        card_type = self.cardTypeListBox.get()
        card_type = card_type.strip()
        set_values.append(card_type)
        # 得到证件号
        set_values.append(self.cardNo.get())
        # 手机号
        set_values.append(self.cellphone.get())

        return set_values

# 订单提交对话框
class ConfirmOrderDialog(Toplevel):
    def __init__(self, parent, prompt_text='', train_info=None, passenger_info=None, okFunc=None, orderParams=None,
                 ht=None):
        Toplevel.__init__(self, parent)
        self.transient(parent)

        self.title('提交订单确认')
        self.parent = parent
        self.result = None
        self.prompt_text = prompt_text
        self.train_info = train_info
        self.passenger_info = passenger_info
        self.okFunc = okFunc
        self.orderParams = orderParams
        self.httpAccessObj = ht

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)
        self.buttonbox()
        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                  parent.winfo_rooty() + 80))
        self.initial_focus.focus_set()
        self.wait_window(self)

    #
    # construction hooks
    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus. 
        title1 = Label(master, text="车次信息", background='#DEE9F5', foreground='#3177BF', font=('黑体', 12, 'normal'),
                       width=83)
        title1.pack(fill=X, pady=5)

        tarin_info_panel = Frame(master)
        tarin_info_panel.pack(fill=X, pady=10)
        for info in self.train_info[0:-1]:
            label = Label(tarin_info_panel, text=info, foreground='#155BA3', font=('黑体', 11, 'bold'))
            label.pack(side=LEFT, padx=3)

        title2 = Label(master, text="乘车人信息", background='#DEE9F5', foreground='#3177BF', font=('黑体', 12, 'normal'))
        title2.pack(fill=X)

        rowHeight = 35
        height = (len(self.passenger_info) + 1) * rowHeight
        border_color = '#9EB6CE'
        passenger_info_canvas = Canvas(master, height=height, background='white')
        passenger_info_canvas.pack(fill=X)
        width = 664
        # 边框
        passenger_info_canvas.create_rectangle(3, 3, width, height, width=1, outline=border_color)
        # 标题
        passenger_info_canvas.create_rectangle(3, 3, width, rowHeight, width=1, outline=border_color,
                                               fill='#E8F0F9')  #E8F0F9
        passenger_info_canvas.create_text(50 / 2 + 3, rowHeight / 2 + 3, text='序号')   # 第一列宽50
        passenger_info_canvas.create_line(53, 3, 53, rowHeight, width=1, fill=border_color)
        passenger_info_canvas.create_text(80 / 2 + 53, rowHeight / 2 + 3, text='席别')   # 第二列宽80
        passenger_info_canvas.create_line(133, 3, 133, rowHeight, width=1, fill=border_color)
        passenger_info_canvas.create_text(80 / 2 + 133, rowHeight / 2 + 3, text='票种')   # 第三列宽80
        passenger_info_canvas.create_line(213, 3, 213, rowHeight, width=1, fill=border_color)
        passenger_info_canvas.create_text(100 / 2 + 213, rowHeight / 2 + 3, text='姓名')   # 第四列宽100
        passenger_info_canvas.create_line(313, 3, 313, rowHeight, width=1, fill=border_color)
        passenger_info_canvas.create_text(80 / 2 + 313, rowHeight / 2 + 3, text='证件类型')   # 第五列宽80
        passenger_info_canvas.create_line(393, 3, 393, rowHeight, width=1, fill=border_color)
        passenger_info_canvas.create_text(150 / 2 + 393, rowHeight / 2 + 3, text='证件号码')   # 第六列宽150
        passenger_info_canvas.create_line(543, 3, 543, rowHeight, width=1, fill=border_color)
        passenger_info_canvas.create_text((width - 543) / 2 + 543, (rowHeight + 3) / 2, text='手机号')
        # 内容
        row = 1
        for info in self.passenger_info:
            if row % 2 == 0: passenger_info_canvas.create_rectangle(3, 3 + row * rowHeight, width,
                                                                    rowHeight * (row + 1), width=1,
                                                                    outline=border_color, fill='#E8F0F9')
            passenger_info_canvas.create_text(50 / 2 + 3, rowHeight / 2 + 3 + row * rowHeight, text=row)   # 第一列宽50
            passenger_info_canvas.create_line(53, row * rowHeight, 53, rowHeight * (row + 1), width=1,
                                              fill=border_color)
            passenger_info_canvas.create_text(80 / 2 + 53, rowHeight / 2 + 3 + row * rowHeight, text=info[0])   # 第二列宽80
            passenger_info_canvas.create_line(133, row * rowHeight, 133, rowHeight * (row + 1), width=1,
                                              fill=border_color)
            passenger_info_canvas.create_text(80 / 2 + 133, rowHeight / 2 + 3 + row * rowHeight,
                                              text=info[1])   # 第三列宽80
            passenger_info_canvas.create_line(213, row * rowHeight, 213, rowHeight * (row + 1), width=1,
                                              fill=border_color)
            passenger_info_canvas.create_text(100 / 2 + 213, rowHeight / 2 + 3 + row * rowHeight,
                                              text=info[2])   # 第四列宽100
            passenger_info_canvas.create_line(313, row * rowHeight, 313, rowHeight * (row + 1), width=1,
                                              fill=border_color)
            passenger_info_canvas.create_text(80 / 2 + 313, rowHeight / 2 + 3 + row * rowHeight,
                                              text=info[3])   # 第五列宽80
            passenger_info_canvas.create_line(393, row * rowHeight, 393, rowHeight * (row + 1), width=1,
                                              fill=border_color)
            passenger_info_canvas.create_text(150 / 2 + 393, rowHeight / 2 + 3 + row * rowHeight,
                                              text=info[4])   # 第六列宽150
            passenger_info_canvas.create_line(543, row * rowHeight, 543, rowHeight * (row + 1), width=1,
                                              fill=border_color)
            passenger_info_canvas.create_text((width - 543) / 2 + 543, rowHeight / 2 + 3 + row * rowHeight,
                                              text=info[5])
            row += 1

        label = Label(master, text="注：系统将根据售出情况随机为您申请席位，暂不支持自选席位。", foreground='#3177BF')
        label.pack(fill=X, pady=5)

        self.prompt_label = Label(master, text=self.prompt_text, foreground='red')
        self.prompt_label.pack(fill=X, pady=5)

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        box = Frame(self)
        w = Button(box, text="取消", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="确认", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    def update_prompt_info(self, text=''):
        self.prompt_label.config(text=text)

    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        self.okFunc(self.orderParams, self.httpAccessObj)
        self.cancel()

    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks
    def validate(self):
        return 1 # override


def main():
    f = open("./resources/order/passengerJson.txt", 'r', encoding="utf-8")
    resultContent = f.read()
    f.close()
    jsonData = json.loads(resultContent)
    rand_image_url = "https://dynamic.12306.cn/otsweb/passCodeNewAction.do?module=login&rand=sjrand"

    f = open("./resources/order/confirm_passenger_init.html", 'r', encoding="utf-8")
    submitResult = f.read()
    f.close()

    parser = order.ParserConfirmPassengerInitPage()
    parser.feed(submitResult)

    comfirmFrame = ConfirmPassengerFrame(contacts=jsonData['passengerJson'], rand_image_url=rand_image_url,
                                         train_info=parser.get_train_info(), seats_info=parser.get_current_seats(),
                                         seats_types=parser.get_seats_types(), ticket_types=parser.get_ticket_types(),
                                         card_types=parser.get_card_types())
    comfirmFrame.submitButton.configure(
        command=lambda: ConfirmOrderDialog(comfirmFrame.root, '提交订单确认', parser.get_train_info(),
                                           comfirmFrame.getPassengerInfo()))
    comfirmFrame.show()


if __name__ == '__main__':
    main()