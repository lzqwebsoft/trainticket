# coding: utf8
import re
import json
import time
import configparser

# 获取默认的列车查询信息
def getDefaultQueryParams():
    defaultQueryParams = {}
    config = configparser.ConfigParser()
    config.read("config.ini")
    try:
        defaultQueryParams['from_station'] = config.get("DefaultQueryInfo", "from_station")
        defaultQueryParams['to_station'] = config.get("DefaultQueryInfo", "to_station")
        defaultQueryParams['train_date'] = config.get("DefaultQueryInfo", "train_date")
    except configparser.NoSectionError:
        print("请设置默认的列车信息在config.ini文件")

    return defaultQueryParams

# 更新城市编码列表数据
def updateCityCode(ht):
    allStationsJsStr = ht.get(url="https://kyfw.12306.cn/otn/resources/js/framework/station_name.js")
    hasStationsRe = re.compile(r'var station_names', re.DOTALL)
    collectStationsRe = re.compile(r'([\"\'])(.+?)\1', re.DOTALL)
    if allStationsJsStr.strip() != "" and hasStationsRe.search(allStationsJsStr):
        collects = collectStationsRe.findall(allStationsJsStr)
        allStationsStr = collects[0][1] if collects and len(collects) > 0 else ''
        collects = allStationsStr.split("@") if allStationsStr else []
        config = configparser.ConfigParser()
        config.read("config.ini")
        if not config.has_section("Stations"):
            config.add_section("Stations")
        for x in collects:
            if x:
                station = x.split('|')
                # ['zzd', '郑州东', 'ZAF', 'zhengzhoudong', 'zzd', '2175']
                config.set('Stations', station[1], station[2])
        fp = open(r'config.ini', 'w')
        config.write(fp)
        fp.close()
    else:
        print('更新获取城市编码列表数据失败！')

# 根据城市名获取对应城市编码
def getAllStationCodes():
    config = configparser.ConfigParser()
    config.read("config.ini")
    try:
        stationCodes = dict(config.items("Stations"))
        return stationCodes
    except configparser.NoSectionError:
        print("车站编码装载失败!")
    return {}

# 得到可预定最大日期
def getMaxPeriod(ht):
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

# 解析查询后的结果集,并根据设置的过滤条件添加额外的条件过滤
def getTrainList(queryResult, filter_params={}):
    trains = []
    train_types = ["G", "D", "Z", "T", "K"]
    filter_train_classes = filter_params.get('trainClass', [])                      # 过滤列车类型
    start_time_range = filter_params.get('start_time', '00:00--24:00').split('--')  # 过滤出发时间
    end_time_range = filter_params.get('end_time', '00:00--24:00').split('--')      # 过滤到达时间
    trainNoStr = filter_params.get('trainNos')
    trainNos = trainNoStr.split(',') if trainNoStr else []                          # 过滤车次号
    trainPassType = filter_params.get('trainPassType')                              # 过始通过类型
    justShowCanBuy = filter_params.get('justShowCanBuy', False)                     # 仅显示可预订列车开关
    if len(queryResult):
        for cvsData in queryResult:
            train_detail_info = cvsData.get('queryLeftNewDTO', {})
            if not train_detail_info: continue
            # ======由用户设定的列车类型过滤列车结果======
            station_train_code = train_detail_info.get('station_train_code')
            start_time = train_detail_info.get('start_time', '00:00')
            end_time = train_detail_info.get('arrive_time', '00:00')
            from_station_name = train_detail_info.get('from_station_name')
            start_station_name = train_detail_info.get('start_station_name')
            canWebBuy = train_detail_info.get('canWebBuy', "N")
            # 过滤不可预订列车
            if justShowCanBuy and canWebBuy == 'N': continue
            if not (station_train_code[:1] in filter_train_classes or (station_train_code[:1] not in train_types and 'QT' in filter_train_classes)): continue
            # 发车时间过滤
            if start_time < start_time_range[0] or start_time > start_time_range[1]: continue
            # 到站时间过滤
            if end_time < end_time_range[0] or end_time > end_time_range[1]: continue
            # 指定车次过滤
            if trainNos and station_train_code not in trainNos: continue
            # 过滤通过类型
            if trainPassType != 'QB':
                if trainPassType == 'SF' and from_station_name != start_station_name: continue
                elif trainPassType == 'LG' and from_station_name == start_station_name: continue
            # =========================================
            train = {}
            # 车次
            train["no"] = station_train_code
            train["no_param"] = train_detail_info.get('train_no')
            # 出站
            train["form_station"] = train_detail_info.get('from_station_name')
            train["start_time"] = start_time
            # 始发站与终到站
            train['start_station'] = train_detail_info.get('start_station_name')
            train['end_station'] = train_detail_info.get('end_station_name')
            # 到站
            train["to_station"] = train_detail_info.get('to_station_name')
            train["end_time"] = train_detail_info.get('arrive_time')
            # 历时
            train["take_time"] = train_detail_info.get('lishi')
            # 各种座位剩余数(商务座,特等座,一等座,二等座,高级软卧,软卧,硬卧,软座,硬座,无座,其他)
            seat_codes = ('swz_num', 'tz_num', 'zy_num', 'ze_num', 'gr_num', 'rw_num', 'yw_num',
                          'rz_num', 'yz_num', 'wz_num', 'qt_num', 'gg_num', 'yb_num')
            for (i, x) in enumerate(seat_codes): train["seat_type" + str(i + 1)] = train_detail_info.get(x)
            # 预定参数
            train['canWebBuy'] = canWebBuy
            train["order_param"] = cvsData.get('secretStr')
            train['buttonTextInfo'] = cvsData.get('buttonTextInfo', '预订')
            trains.append(train)
    return trains

# 由发站名、到站名、列车日期访问网络获取对应符合条件列车信息
# URL: https://kyfw.12306.cn/otn/leftTicket/query
# GET参数(顺序很重要):
#    leftTicketDTO.from_station=SHH      始发站
#    leftTicketDTO.to_station=WHN        终点站
#    leftTicketDTO.train_date=2014-01-25 出发日期
#    purpose_codes=ADULT                 对应的身份标只，查看是否是学生
# 返回结果为JSON
def queryTrains(ht, query_params={}):
    if not query_params.get('trainClass'):
        print('查询失败，请选择列车类型')
        return []
    train_date = query_params.get('train_date', time.strftime("%Y-%m-%d", time.localtime()))
    from_station = query_params.get('from_station')
    to_station = query_params.get('to_station')
    if from_station and to_station:
        purposeCodes = getPurposeCodes(False)
        selectParams = [("leftTicketDTO.train_date", train_date),
                        ("leftTicketDTO.from_station", from_station),
                        ("leftTicketDTO.to_station", to_station),
                        ("purpose_codes", purposeCodes)]

        queryResult = ht.get(url="https://kyfw.12306.cn/otn/leftTicket/query", params=selectParams)
        try:
            query_data = json.loads(queryResult)
            train_data = query_data.get('data', {}) if type(query_data) == dict else {}
            if train_data:
                # 解析整理得到的列车数据
                trains = getTrainList(train_data, filter_params=query_params)
                if trains != None and len(trains) > 0:
                    return trains
            else:
                if 'messages' in query_data and query_data['messages']:
                    print(query_data['messages'])
                else:
                    print(queryResult)
                print('查询失败')
        except TypeError:
            print('查询失败')
    else:
        print('查询失败，请设置出发地与目的地')
    return []