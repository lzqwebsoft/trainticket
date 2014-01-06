# coding: utf8
import re
import json
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
    if allStationsJsStr.strip() != "" and hasStationsRe.search(allStationsJsStr):
        collects = collectStationsRe.findall(allStationsJsStr)
        allStationsStr = collects[0]
        collects = allStationsStr.split("@")
        config = configparser.SafeConfigParser()
        config.read("config.ini")
        if not config.has_section("Stations"):
            config.add_section("Stations")
        stations = []
        for x in collects:
            if x.strip() != '':
                titem = x.split('|')
                # ['zzd', '郑州东', 'ZAF', 'zhengzhoudong', 'zzd', '2175']
                config.set('Stations', titem[1], titem[2])
        fp = open(r'config.ini', 'w')
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
        if cityCode.strip() != '':
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
    if len(collects) == 1:
        minPeriodRe = collects[0]
    return minPeriodRe

# 根据判断是否是学生，得到对应的purposeCodes码，用于查询
def getPurposeCodes(is_sutdent):
    if is_sutdent:
        return "0X00"
    else:
        return "ADULT"

# 模仿点击余票查询后，增加后台日志
def logQuery(ht, queryParams):
    queryParams = [('method', 'qt')] + queryParams
    print(queryParams)
    content = ht.get(url="https://dynamic.12306.cn/otsweb/order/querySingleAction.do", params=queryParams)
    print(content)

# 解析查询后的结果集,得到所有列车列表数据
def getTrainList(queryResult):
    trains = []
    if len(queryResult) > 0:
        for cvsData in queryResult:
            train = {}
            train_detail_info = cvsData['queryLeftNewDTO']
            # 车次
            train["no"] = train_detail_info['station_train_code']
            train["no_param"] = train_detail_info['train_no']
            # 发站
            train["form_station"] = train_detail_info['start_station_name']
            train["start_time"] = train_detail_info['start_time']
            # 到站
            train["to_station"] = train_detail_info['to_station_name']
            train["end_time"] = train_detail_info['arrive_time']
            # 历时
            train["take_time"] = train_detail_info['lishi']
            # 各种座位剩余数(商务座,特等座,一等座,二等座,高级软卧,软卧,硬卧,软座,硬座,无座,其他)
            seat_codes = ('swz_num', 'tz_num', 'zy_num', 'ze_num', 'gr_num', 'rw_num', 'yw_num',
                          'rz_num', 'yz_num', 'wz_num', 'qt_num', 'gg_num' ,'yb_num')
            for (i, x) in enumerate(seat_codes):
                train["seat_type" + str(i+1)] = train_detail_info[x]
            # 预定参数
            train["order_param"] = ""
            if cvsData['secretStr']:
                train["order_param"] = cvsData['secretStr']
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

"""
https://kyfw.12306.cn/otn/leftTicket/query
    leftTicketDTO.from_station=SHH   始发站
    leftTicketDTO.to_station=WHN     终点站
    leftTicketDTO.train_date=2014-01-25 出发日期
    purpose_codes=ADULT    对应的身份标只，查看是否是学生
    """
def queryTrains(ht, from_station, to_station, train_date=None, start_time="00:00--24:00", trainClass="QB#D#Z#T#K#QT#",
                trainPassType="QB"):
    if not train_date: train_date = time.strftime("%Y-%m-%d", time.localtime())
    fromStation = getCityCodeByName(from_station)
    toStation = getCityCodeByName(to_station)
    purposeCodes = getPurposeCodes(False)
    selectParams = [("leftTicketDTO.train_date", train_date),
                    ("leftTicketDTO.from_station", fromStation),
                    ("leftTicketDTO.to_station", toStation),
                    ("purpose_codes", purposeCodes)]

    queryResult = ht.get(url="https://kyfw.12306.cn/otn/leftTicket/query", params=selectParams)
    query_data = json.loads(queryResult)
    if type(query_data)==dict and query_data['data'] and len(query_data['data']) > 0:
        # 解析整理得到的列车数据
        trains = getTrainList(query_data['data'])
        if trains!=None and len(trains) > 0:
            return trains
    else:
        print(queryResult)
        print('查询失败')
    return []