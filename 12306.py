# -*- coding:utf-8 -*-
__author__ = 'admin-yj'

import urllib
import urllib2
import ssl
import re
import cookielib
from user import name, passworld
from rk import getCode
from json import loads
from cons import stationDict
from time import sleep

# 出发时间
train_date = '2018-07-20'
# 出发城市
fromStation = '长沙'
from_station = stationDict[fromStation]
# 到达城市
toStation = '成都'
to_station = stationDict[toStation]
# 乘客姓名
passenger_Name = '###'
# 座位类型
seatType = '3'

c = cookielib.LWPCookieJar()  # 生成一个存储cookie的对象
cookie = urllib2.HTTPCookieProcessor(c)
opener = urllib2.build_opener(cookie)  # 把存储器绑定到opener对象当中
urllib2.install_opener(opener)

# 添加浏览器标识，简单的反爬
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/67.0.3396.99 Safari/537.36'
}
# 跳过证书验证
ssl._create_default_https_context = ssl._create_unverified_context


def login():
    # 请求验证码
    print '正在请求验证码'
    req = urllib2.Request(
        'https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand&0.270868105120873')
    req.headers = header
    imgCode = opener.open(req).read()  # 将验证码图片本地存储
    with open('code.png', 'wb') as fn:
        fn.write(imgCode)

    # 校验验证码
    print '正在识别验证码'
    req = urllib2.Request(
        'https://kyfw.12306.cn/passport/captcha/captcha-check'
    )
    req.headers = header
    code = getCode()  # 通过打码平台获得验证码
    data = {
        'answer': code,
        'login_site': 'E',
        'rand': 'sjrand'
    }
    data = urllib.urlencode(data)
    html = opener.open(req, data).read()
    if loads(html)['result_code'] == '4':
        print "验证码校验成功"
    else:
        login()

    # 校验账号、密码
    print '正在登录'
    req = urllib2.Request(
        'https://kyfw.12306.cn/passport/web/login')
    req.headers = header
    data = {
        'username': name,
        'password': passworld,
        'appid': 'otn'
    }
    data = urllib.urlencode(data)
    opener.open(req, data)

    # 第一步骤
    req = urllib2.Request('https://kyfw.12306.cn/otn/login/userLogin')
    req.headers = header
    data = {
        '_json_att': ''
    }
    data = urllib.urlencode(data)
    opener.open(req, data)
    # 第二步骤
    req = urllib2.Request('https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin')
    req.headers = header
    data = {
        'redirect': '/otn/login/userLogin'
    }
    data = urllib.urlencode(data)
    opener.open(req, data)
    # 第三步骤
    req = urllib2.Request('https://kyfw.12306.cn/passport/web/auth/uamtk')
    req.headers = header
    data = {
        'appid': 'otn'
    }
    data = urllib.urlencode(data)
    result = loads(opener.open(req, data).read())
    tk = result['newapptk']
    # 第四步骤
    req = urllib2.Request('https://kyfw.12306.cn/otn/uamauthclient')
    req.headers = header
    data = {
        'tk': tk
    }
    data = urllib.urlencode(data)
    result = loads(opener.open(req, data).read())

    if result['result_code'] == 0:
        print '登录成功'
        return True

    print '登录失败，正在尝试重新登录'
    sleep(5)
    login()  # 递归，重复直至成功登录


def checkTickets():
    # 这是一个 get 请求，明文传输，提供参数
    req = urllib2.Request(
        'https://kyfw.12306.cn/otn/leftTicket/query?leftTicketDTO.train_date=%s&leftTicketDTO.from_station=%s'
        '&leftTicketDTO.to_station=%s&purpose_codes=ADULT ' % (train_date, from_station, to_station)
    )
    req.headers = header
    html = opener.open(req).read()
    result = loads(html)

    '''
    各个字段代表的信息：
    [3]:车次
    [8]:出发时间
    [9]:到达时间
    [10]:历时
    [23]:软卧
    [26]:无座
    [27]:
    [28]:硬卧
    [29]:硬座
    [30]:二等座
    [31]:一等座
    [32]:商务特等座
    '''
    tickerList = []
    for i in result['data']['result']:
        temList = i.split('|')
        try:
            if temList[29] == u'有' or int(temList[29]) > 0:
                tickerList.append(temList[0])
                print u'''
                    该车次有二等座票:
                    车次：%s
                    出发时间：%s
                    到达时间：%s
                    历时：%s
                    余票：%s
                    ''' % (temList[3], temList[8], temList[9], temList[10], temList[29])
                break
        except:  # 跳过无票的车次
            continue
    return tickerList[0]


def buyTicket(secretStr):
    # 发出第一个请求
    req = urllib2.Request('https://kyfw.12306.cn/otn/login/checkUser')
    req.header = header
    data = {
        '_json_att': ''
    }
    data = urllib.urlencode(data)
    opener.open(req, data)
    print '第一个请求', opener.open(req, data).read()

    # 发出第二个请求
    req = urllib2.Request('https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest')
    req.header = header
    data = {
        'secretStr': urllib.unquote(secretStr),
        'train_date': train_date,
        'back_train_date': '2018-07-22',
        'tour_flag': 'wc',
        'purpose_codes': 'ADULT',
        'query_from_station_name': fromStation,
        'query_to_station_name': toStation,
        'undefined': ''
    }
    data = urllib.urlencode(data)
    opener.open(req, data)
    print '第二个请求', opener.open(req, data).read()

    # 发出第三个请求
    req = urllib2.Request('https://kyfw.12306.cn/otn/confirmPassenger/initDc')
    req.header = header
    data = {
        '_json_att': ''
    }
    data = urllib.urlencode(data)
    html = opener.open(req, data).read()
    globalRepeatSubmitToken = re.findall(r"globalRepeatSubmitToken = '(.*?)'", html)[0]
    print '第三个请求', globalRepeatSubmitToken

    # 发出四个请求
    req = urllib2.Request('https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs')
    req.header = header
    data = {
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': globalRepeatSubmitToken
    }
    data = urllib.urlencode(data)
    opener.open(req, data)
    print '第四个请求', opener.open(req, data).read()

    # 处理乘客的相关信息
    # result = loads(opener.open(req, data).read())
    # passengerDic = {}
    # for i in result['data']['normal_passengers']:
    #     if i['passenger_name'] == passenger_Name.decode('utf-8'):
    #         passengerDic = i
    #         break

    ''''
    座位类型说明
    商务座：9
    一等座：M
    二等座：O（字母）
    高级软卧：6
    软卧：4
    动卧：F
    硬卧：3
    软座：2
    硬座：1
    无座：
    其他：
    '''
    # oldPassengerStr = passengerDic['passenger_name'] + ',1,' + passengerDic['passenger_id_no'] + ',' + '1_'
    # print oldPassengerStr
    # passengerTicketStr = seatType + ',0,1,' + passengerDic['passenger_name'] + ',1,' + passengerDic[
    #     'passenger_id_no'] + ',' + passengerDic['mobile_no'] + ',N'
    # print passengerTicketStr
    #

    # req = urllib2.Request('https://kyfw.12306.cn/otn/index/initMy12306')
    # req.headers = header
    # print opener.open(req).read()
    for i in c:
        print i
    # 发出五个请求
    req = urllib2.Request('https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo')
    headerTmp = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/67.0.3396.99 Safari/537.36',
        'Host': 'kyfw.12306.cn',
        'Origin:': 'https://kyfw.12306.cn',
        'Referer': 'https://kyfw.12306.cn/otn/confirmPassenger/initDc',
        'X-Requested-With': 'XMLHttpRequest',
    }

    req.header = headerTmp

    data = {
        '_json_att': '',
        'bed_level_order_num': '000000000000000000000000000000',
        'cancel_flag': '2',
        'passengerTicketStr': 'O,0,1,李祥日,1,370722197210017217,15964561632,N', # passengerTicketStr,O,0,1,徐红喜,1,370181199008211725,18764691430N
        'oldPassengerStr': '李祥日,1,370722197210017217,1_',  # oldPassengerStr,
        'randCode': '',
        'REPEAT_SUBMIT_TOKEN': globalRepeatSubmitToken,
        'tour_flag': 'dc',
        'whatsSelect': '1'
    }

    data = urllib.urlencode(data)
    html = opener.open(req, data)
    print '第五个请求', html.read()
    print html.getcode(), html.geturl()
    for i in c:
        print i

login()
secretStr = checkTickets()  # 注意，这里需要获取一个代表车次的加密字符串
buyTicket(secretStr)
