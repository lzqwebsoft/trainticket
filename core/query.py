# coding: utf8
import re
import time
from common.httpaccess import HttpTester
try:
    # Python2
    import ConfigParser as configparser
except ImportError:
    # Python3
    import configparser

# 更新城市编码列表数据
def updateCityCode(ht):
    allStationsJsStr = ht.get(url="https://kyfw.12306.cn/otn/resources/merged/station_name_js.js")
    hasStationsRe = re.compile(r'var station_names', re.DOTALL)
    collectStationsRe = re.compile(r'"(.+?)"', re.DOTALL)
    if allStationsJsStr.strip()!="" and hasStationsRe.search(allStationsJsStr):
        collects = collectStationsRe.findall(allStationsJsStr)
        allStationsStr = collects[0]
        collects = allStationsStr.split("@")
        config = configparser.SafeConfigParser()
        config.read("config.ini")
        if not config.has_section("Stations"):
            config.add_section("Stations")
        stations = []
        for x in collects:
            if x.strip()!='':
                titem = x.split('|')
                # ['zzd', '郑州东', 'ZAF', 'zhengzhoudong', 'zzd', '2175']
                config.set('Stations', titem[1], titem[2])
        fp = open(r'config.ini','w')
        config.write(fp)
        fp.close()
    else:
        print('更新获取城市编码列表数据失败！')

# 根据城市名获取对应城市编码
def getCityCodeByName(cityName):
    config = configparser.SafeConfigParser()
    config.read("config.ini")
    try:
        cityCode = config.get("Stations", cityName)
        if cityCode.strip()!='':
            return cityCode
    except configparser.NoSectionError:
        print("没有对应城市：%s" % cityName)
    return ''

# 得到可预定最大日期
def getMaxPeriod(httpaccess):
    queryInitStr = ht.get(url='https://dynamic.12306.cn/otsweb/order/querySingleAction.do', params={"method": "init"})
    # var maxPeriod = '2013-11-26 10:38:38';
    # var minPeriod = '2013-11-07 10:38:38'; 
    maxPeriodRe = re.compile(r'var maxPeriod\S*?=\S*?\'(.+?)\';', re.DOTALL)
    # 最小的时间范围是否需要，应该为当前时间
    # minPeriodRe = re.compile(r'var minPeriod\s*?=\s*?\'(.+?)\';', re.DOTALL)
    minPeriodRe = None
    collects = maxPeriodRe.findall(queryInitStr)
    if len(collects)==1:
        minPeriodRe = collects[0]
    return minPeriodRe

# 模仿点击余票查询后，增加后台日志
def logQuery(ht, queryParams):
    queryParams = [('method','qt')] + queryParams
    print(queryParams)
    content = ht.get(url="https://dynamic.12306.cn/otsweb/order/querySingleAction.do", params=queryParams)
    print(content)

# 解析查询后的结果集,得到所有列车列表数据
def getTrainList(queryResult):
    trains = []
    result = queryResult.split("\\n")
    if len(result) > 0:
        # 获取列车号的正则表达式
        numRe = re.compile(r'<span.+?onmouseover=javascript:onStopHover\(\'(.+?)\'\).*?>(.+?)</span>', re.DOTALL)
        # 去除HTML标检的正则表达式
        removeHTMLRe = re.compile(r'</?\w+[^>]*>', re.DOTALL)
        # 得到预约参数正则表达式
        orderTrainRe = re.compile(r'<a.+?onclick=javascript:getSelected\(\'(.+?)\'\).*?>.+?</a>', re.DOTALL)
        for cvsData in result:
            # 去掉HTML中的空格
            cvsData = cvsData.replace("&nbsp;", "")
            item = cvsData.split(",")
            if len(item)!=17:
                continue
            train = {}
            # 车次
            numbers = numRe.findall(item[1])
            train["no"] = numbers[0][1]
            train["no_param"] = numbers[0][0]
            # 发站
            from_station_info = item[2].split("<br>")
            train["form_station"] = removeHTMLRe.sub("", from_station_info[0])
            train["start_time"] = removeHTMLRe.sub("", from_station_info[1])
            # 到站
            to_station_info = item[3].split("<br>")
            train["to_station"] = removeHTMLRe.sub("", to_station_info[0])
            train["end_time"] = removeHTMLRe.sub("", to_station_info[1])
            # 历时
            train["take_time"] = removeHTMLRe.sub("", item[4])
            # 各种座位剩余数(商务座,特等座,一等座,二等座,高级软卧,软卧,硬卧,软座,硬座,无座,其他)
            for x in range(5, 16):
                train["seat_type"+str(x-4)] = removeHTMLRe.sub("", item[x])
            # 预定参数
            train["order_param"] = ""
            if orderTrainRe.search(item[16]):
                temp = orderTrainRe.findall(item[16])
                train["order_param"] = temp[0]
            trains.append(train)
    return trains

"""
由设置的请求参数得到对应查询的列车列表数据,对应参数如下:
URL:
    https://dynamic.12306.cn/otsweb/order/querySingleAction.do
GET参数(顺序很重要): 
    method = queryLeftTicket
    orderRequest.train_date = 2013-11-15
    orderRequest.from_station_telecode = KXM
    orderRequest.to_station_telecode =  SHH
    orderRequest.train_no =
    trainPassType = QB              (全部，始化，过路)(QB, SF, GL)
    rainClass = QB#D#Z#T#K#QT#      (全部，动车，Z字头，T字头，K字头, 其它)
    includeStudent = 00             (学生：0X00， 成人：00)
    seatTypeAndNum =
    orderRequest.start_time_str = 00:00--24:00
"""
def queryTrains(ht, from_station, to_station, train_date = None, start_time = "00:00--24:00", trainClass="QB#D#Z#T#K#QT#", trainPassType="QB"):
    if not train_date: train_date = time.strftime("%Y-%m-%d", time.localtime())
    fromStation = getCityCodeByName(from_station)
    toStation = getCityCodeByName(to_station)
    selectParams = [("orderRequest.train_date", train_date),
                    ("orderRequest.from_station_telecode", fromStation),
                    ("orderRequest.to_station_telecode", toStation),
                    ("orderRequest.train_no", ""),
                    ("trainPassType", trainPassType),
                    ("trainClass", trainClass),
                    ("includeStudent", "00"),
                    ("seatTypeAndNum", ""),
                    ("orderRequest.start_time_str", start_time)]
    """
    leftTicketDTO.from_station=SHH
    leftTicketDTO.to_station=WHN
    leftTicketDTO.train_date=2014-01-25
    purpose_codes=ADULT
    """
    #logQuery(ht, selectParams)
    selectParams = [('method','queryLeftTicket')] + selectParams
    queryResult = ht.get(url="https://kyfw.12306.cn/otn/leftTicket/query", params=selectParams)
    if queryResult == "-10":
        print("您还没有登录或者离开页面的时间过长，请登录系统或者刷新页面")
    elif queryResult == "-1":
        print("服务器忙，加载查询数据失败！")
    elif queryResult!=None and queryResult.split(",")[0]=="-2":
        print(queryResult.split(",")[1])
    else:
        # 将得到的字符串以\n字符分割
        trains = getTrainList(queryResult)
        if trains!=None and len(trains) > 0:
            return trains
    return []