# coding: utf8
import random
try:
    # Python2
    from Tkinter import *
    from ttk import *
except ImportError:
    # Python3
    from tkinter import *
    from tkinter.ttk import *

class QueryTrainFrame:
    def __init__(self, initQueryParams={}):
        self.root = Tk()
        self.root.title("列车查询")

        self.root['padx'] = 20
        self.root['pady'] = 20

        conditionPanel = Frame(self.root, height=150, width=750, borderwidth=1, relief=GROOVE)
        conditionPanel.pack()

        fromStationLabel = Label(conditionPanel, text="*出发地:")
        fromStationLabel.place(x = 10, y = 10, width=50, height=25)
        self.fromStation = Entry(conditionPanel)
        default_from_station = initQueryParams.get('from_station', '')
        self.fromStation.insert(0, default_from_station)
        self.fromStation.place(x = 70, y = 10, width=100, height=23)

        toStationLabel = Label(conditionPanel, text="*目的地:")
        toStationLabel.place(x = 180, y = 10, width=50, height=25)
        self.toStation = Entry(conditionPanel)
        default_to_station = initQueryParams.get('to_station', '')
        self.toStation.insert(0, default_to_station)
        self.toStation.place(x = 240, y = 10, width=100, height=23)

        trainDateLabel = Label(conditionPanel, text="*出发日期:")
        trainDateLabel.place(x = 360, y = 10, width=60, height=25)
        self.trainDate = Entry(conditionPanel)
        default_train_date = initQueryParams.get('train_date', '')
        self.trainDate.insert(0, default_train_date)
        self.trainDate.place(x = 430, y = 10, width=120, height=23)

        startDateLabel = Label(conditionPanel, text="出发时间:")
        startDateLabel.place(x = 560, y = 10, width=60, height=25)
        self.startTime = Combobox(conditionPanel, values=["00:00--24:00", "00:00--06:00", "06:00--12:00", "12:00--18:00", "18:00--24:00"], state="readonly")
        self.startTime.set("00:00--24:00")   # 设置默认时间
        self.startTime.place(x = 620, y = 10, width=100, height=23)

        endTimeLabel = Label(conditionPanel, text="到达时间:")
        endTimeLabel.place(x = 560, y = 45, width=60, height=25)
        self.endTime = Combobox(conditionPanel, values=["00:00--24:00", "00:00--06:00", "06:00--12:00", "12:00--18:00", "18:00--24:00"], state="readonly")
        self.endTime.set("00:00--24:00")   # 设置默认时间
        self.endTime.place(x = 620, y = 45, width=100, height=23)

        trainNoLabel = Label(conditionPanel, text="出发车次:")
        trainNoLabel.place(x = 10, y = 45, width=60, height=25)
        self.trainNo = Entry(conditionPanel, width=30)
        self.trainNo.place(x = 70, y = 45, width=270, height=23)

        # 过滤空列车开关
        self.showCanBuySwitch = IntVar()
        showCanBuyCheckButton = Checkbutton(conditionPanel, text='仅显示可预订车次', variable=self.showCanBuySwitch)
        # self.autoQuerySwitch.set(1)
        showCanBuyCheckButton.place(x=430, y=45, width=120, height=23)

        # 列车类型
        allTrainClass = ['G-高铁', 'D-动车', 'Z-直达', 'T-特快', 'K-快速', '其它']
        self.trainClassValue = ["G", "D", "Z", "T", "K", 'QT']
        index = 3
        self.vars = []
        for trainClassText in allTrainClass:
            var = IntVar()
            index += 1
            chk = Checkbutton(conditionPanel, text=trainClassText, variable=var)
            var.set(1)   # 设置选中
            chk.place(x = 10 + (index-4)*68, y = 78, width=64, height=23)
            self.vars.append(var)

        # 列车站点经过类型
        trainPassType = [("全部", 0), ("始发", 1), ("路过", 2)]
        self.trainPassTypeValue = ["QB", "SF", "LG"]
        self.trainPassTypeVar = IntVar()
        index = index + 4
        for text, value in trainPassType:
            index += 1
            radiobutton = Radiobutton(conditionPanel, text=text, variable=self.trainPassTypeVar, value=value)
            radiobutton.place(x = 200 + (index-9)*50, y = 78, width=55, height=23)

        # 自动查询开关
        self.autoQuerySwitch = IntVar()
        autoQueryCheckButton = Checkbutton(conditionPanel, text='自动查询', variable=self.autoQuerySwitch)
        # self.autoQuerySwitch.set(1)
        autoQueryCheckButton.place(x=650, y=78, width=70, height=23)

        self.selectButton = Button(conditionPanel, text="查询")
        self.selectButton.place(x = 650, y = 110, width=70, height=25)

        # 中间信息提示面板
        infoPanel = Frame(self.root, height=70, width=750)
        infoPanel.pack()

        self.infoStartDateLabel = Label(infoPanel) # "出发日期：2013-11-15 上海->武汉(共 30 趟列车)"
        self.infoStartDateLabel.place(x = 0, y = 2, width=300, height=25)
        infoLabel = Label(infoPanel, text="“有”：票源充足  “无”：票已售完  “*”：未到起售时间 “--”：无此席别", foreground='blue')
        infoLabel.place(x = 320, y = 2, width=430, height=25)

        # 查询结果表头
        tableHead = ResultTableHead(infoPanel)
        tableHead.place(x = 0, y = 30, width=733, height=42)
        tableHead.create_rectangle(2, 2, 730, 40, outline="#93AFBA")

        # 查询结果内容面板
        contentPanel = Frame(self.root)

        yscrollbar = Scrollbar(self.root)
        yscrollbar.pack(side=RIGHT, fill=Y)
        self.resultTable = ResultTable(contentPanel)
        self.resultTable.configure(yscrollcommand=yscrollbar.set)
        self.resultTable.pack(expand=YES, fill=Y)
        yscrollbar.config(command=self.resultTable.yview)

        contentPanel.pack(expand=YES, fill=BOTH)

    def getSelectedTrainTime(self):
        starttime = self.startTime.get()
        return starttime

    def getSelectedTrainClass(self):
        result = list(map((lambda var: var.get()), self.vars))
        train_classes = [self.trainClassValue[i] for i, x in enumerate(result) if x]
        return train_classes

    def getChoiceTrainPassType(self):
        index = self.trainPassTypeVar.get()
        if index!=None:
            return self.trainPassTypeValue[index]
        return self.trainPassTypeValue[0]

    def showSelectedTrainClass(self):
        temp = random.randint(1, 15)
        self.resultTable.updateResult(temp)
        print(self.getSelectedTrainTime())
        print(self.getSelectedTrainClass())
        print(self.getChoiceTrainPassType())

    def show(self):
        width = 790
        height = 600
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = int((ws/2) - (width/2) )
        y = int((hs/2) - (height/2) )
        self.root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        self.root.resizable(False, False)
        self.root.mainloop()

    def quit(self):
        self.root.destroy()

class ResultTableHead(Canvas):
    def __init__(self, parent, width=750, height=42, columnHeigth=42, background='#E5F2F8', borderColor='#93AFBA'):
        Canvas.__init__(self, parent, bd=0, background=background, width=width)
        self.borderColor = borderColor
        self.columnHeigth = columnHeigth

        self.create_line(2, 0, 1, 0, width=1, fill=self.borderColor)        # 第一列宽度50
        self.create_text(25, self.columnHeigth/2, text="车次")

        self.create_line(52, 0, 52, self.columnHeigth, width=1, fill=self.borderColor)      # 第二列宽度65
        self.create_text(52+65/2, self.columnHeigth/2, text="发站")

        self.create_line(117, 0, 117, self.columnHeigth, width=1, fill=self.borderColor)    # 第三列宽度65
        self.create_text(117+65/2, self.columnHeigth/2, text="到站")

        self.create_line(182, 0, 182, self.columnHeigth, width=1, fill=self.borderColor)    # 第四列宽度50
        self.create_text(182+25, self.columnHeigth/2, text="历时")

        # 如下其余宽度40
        seatType = ["商务座", "特等座", "一等座", "二等座", "高级软卧", "软卧", "硬卧", "软座", "硬座", "无座", "其它"]
        for column in range(11):
            self.create_line(column*40+232, 0, column*40+232, self.columnHeigth, width=1, fill=self.borderColor)
            if column!=4:
                self.create_text(column*40+232+40/2, self.columnHeigth/2, text=seatType[column])
            else:
                self.create_text(column*40+232+10, self.columnHeigth/2, text="高级", anchor=SW)
                self.create_text(column*40+232+10, self.columnHeigth/2, text="软卧", anchor=NW)
        self.create_line(11*40+232, 0, 11*40+232, self.columnHeigth, width=1, fill=self.borderColor)

        self.create_line(width-1, 0, width-1, self.columnHeigth, width=1, fill=self.borderColor)

        self.create_line(0, 0, width, 0, width=1, fill=self.borderColor)
        self.create_line(0, 0, width, 0, width=1, fill=self.borderColor)


class ResultTable(Canvas):
    def __init__(self, parent, width=730, columnHeigth=35, borderColor='#93AFBA'):
        if columnHeigth<30: columnHeigth=30   # 设置列高的最小宽度是30
        Canvas.__init__(self, parent, bd=0, background='white', width=width)
        self.width = width
        self.parent = parent
        self.columnHeigth = columnHeigth
        self.borderColor = borderColor
        # height = self.winfo_height()
        # self.create_rectangle(0, 0, width, height, outline='blue')
        self._widgets = []

    def updateResult(self, trainDatas=[], orderHandleFuc=None):
        self.delete(ALL) # remove all items
        rows = len(trainDatas)
        if rows <= 0: return
        self.configure(scrollregion=(0,0,730, rows*self.columnHeigth+3))
        for row, trainData in enumerate(trainDatas):
            labelBg = "white"
            if row % 2 != 0:
                self.create_rectangle(1, row*self.columnHeigth, self.width-1, (row+1)*self.columnHeigth, fill='#E5F2F8')
                labelBg = "#E5F2F8"

            self.create_line(1, row*self.columnHeigth, 1, (row+1)*self.columnHeigth, width=1, fill=self.borderColor)        # 第一列宽度50
            numberLable = Label(self.parent, text=trainData['no'], foreground='blue', cursor="mouse", background=labelBg)
            self.create_window(5, row*self.columnHeigth+(self.columnHeigth-25)/2, anchor=NW, window=numberLable, height=25)

            # 使用颜色标记过站
            form_station_color = 'black' if trainData['form_station'] == trainData['start_station'] else 'red'
            self.create_line(51, row*self.columnHeigth, 51, (row+1)*self.columnHeigth, width=1, fill=self.borderColor)      # 第二列宽度65
            self.create_text(51+5, row*self.columnHeigth+self.columnHeigth/2, text=trainData['form_station'], fill=form_station_color, anchor=SW)
            self.create_text(51+5, row*self.columnHeigth+self.columnHeigth/2, text=trainData['start_time'],  anchor=NW)

            to_station_color = 'black' if trainData['to_station'] == trainData['end_station'] else 'red'
            self.create_line(116, row*self.columnHeigth, 116, (row+1)*self.columnHeigth, width=1, fill=self.borderColor)    # 第三列宽度65
            self.create_text(116+5, row*self.columnHeigth+self.columnHeigth/2, text=trainData["to_station"], fill=to_station_color, anchor=SW)
            self.create_text(116+5, row*self.columnHeigth+self.columnHeigth/2, text=trainData['end_time'], anchor=NW)

            self.create_line(181, row*self.columnHeigth, 181, (row+1)*self.columnHeigth, width=1, fill=self.borderColor)    # 第四列宽度50
            self.create_text(181+25, row*self.columnHeigth+self.columnHeigth/2, text=trainData["take_time"])

            # 如下其余宽度40
            for column in range(11):
                self.create_line(column*40+231, row*self.columnHeigth, column*40+231, (row+1)*self.columnHeigth, width=1, fill=self.borderColor)
                seatColor = "black"
                seatNumInfo = trainData["seat_type"+str(column+1)]
                if seatNumInfo=="有": seatColor = "green"
                self.create_text(column*40+231+40/2, row*self.columnHeigth+self.columnHeigth/2, text=seatNumInfo, fill=seatColor)
            self.create_line(11*40+231, row*self.columnHeigth, 11*40+231, (row+1)*self.columnHeigth, width=1, fill=self.borderColor)
            orderButtonState = DISABLED
            if trainData["canWebBuy"] == 'Y':
                orderButtonState = NORMAL
            if trainData["buttonTextInfo"]=='预订':
                orderButton = Button(self.parent, text = "预订", state=orderButtonState, command=lambda order_param=trainData["order_param"]: orderHandleFuc(order_param))
                self.create_window(self.width-55, row*self.columnHeigth+(self.columnHeigth-25)/2, anchor=NW, window=orderButton, height=25, width=50)
            else:
                buttonTextInfo = trainData["buttonTextInfo"].split('<br/>')
                if len(buttonTextInfo)==1:
                    self.create_text(self.width-60/2, row*self.columnHeigth+self.columnHeigth/2, text=trainData["buttonTextInfo"], fill="black")
                elif len(buttonTextInfo)==2:
                    self.create_text(self.width-55, row*self.columnHeigth+self.columnHeigth/2, text=buttonTextInfo[0], fill="black", anchor=SW)
                    self.create_text(self.width-55, row*self.columnHeigth+self.columnHeigth/2, text=buttonTextInfo[1], fill="black", anchor=NW)
            self.create_line(self.width-1, row*self.columnHeigth, self.width-1, (row+1)*self.columnHeigth, width=1, fill=self.borderColor)

            self.create_line(0, row*self.columnHeigth, self.width, row*self.columnHeigth, width=1, fill=self.borderColor)
        self.create_line(0, rows*self.columnHeigth, self.width, rows*self.columnHeigth, width=1, fill=self.borderColor)

def main():
    frame = QueryTrainFrame()
    frame.show()

if __name__ == '__main__':
    main()


