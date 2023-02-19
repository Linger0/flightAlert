import json
import requests
import time
import math
from datetime import datetime

def pushMessage(messagetitle, messagecontent, tokens):
    for tok in tokens:
        sendUrl = f'https://sctapi.ftqq.com/{tok}.send'
        sendData = {'title': messagetitle, 'content': messagecontent}
        # print(messageTitle)
        # print(messageContent)
        requests.post(sendUrl, data=sendData)

def processData(results):
    result_goto, result_back = results
    price_goto_dict = {}
    price_back_dict = {}
    for i_date in result_goto:
        day = datetime.strptime(i_date, "%Y%m%d")
        day_delta = day - datetime.today()
        if day_delta.days >= 60:
            break
        day_weekday = day.weekday() + 1
        if day_weekday >= 4: # skip Monday to Wednesday
            price_goto_dict[day.strftime("%m-%d") + r"(" + str(day_weekday) + r")"] = result_goto[i_date]
            price_back_dict[day.strftime("%m-%d") + r"(" + str(day_weekday) + r")"] = result_back[i_date]

    min_goto_price = min(price_goto_dict.values())
    dateWithMin = [x for x in price_goto_dict if price_goto_dict[x] == min_goto_price]

    title = f'当前低价: {min_goto_price} ' + dateWithMin[0]
    content = "### " + " ".join(dateWithMin)
    content += "\n\n所有日期价格:\n\n&emsp;&emsp;&emsp;&emsp;SHA–BJS&ensp;BJS–SHA\n\n---"
    for i_date in price_goto_dict:
        content += "\n\n"
        day_weekday = i_date[6]
        content += i_date + ":&emsp;" \
            + ("**" if price_goto_dict[i_date] <= min_goto_price else "") \
            + str(price_goto_dict[i_date]) \
            + ("**" if price_goto_dict[i_date] <= min_goto_price else "") \
            + "&emsp;&emsp;&emsp;" \
            + ("**" if price_back_dict[i_date] <= min_goto_price else "") \
            + str(price_back_dict[i_date]) \
            + ("**" if price_back_dict[i_date] <= min_goto_price else "")
        if day_weekday == "7":
            content += "\n\n---"

    return title, content, min_goto_price

if __name__ == "__main__":
    # first import the json config file
    with open("config.json") as f:
        config = json.load(f)
    # assemble the request url
    baseUrl = "https://flights.ctrip.com/itinerary/api/12808/lowestPrice?"
    url_goto = f'https://flights.ctrip.com/itinerary/api/12808/lowestPrice?flightWay={config["flightWay"]}&dcity={config["placeFrom"]}&acity={config["placeTo"]}&direct=true&army=false'
    url_back = f'https://flights.ctrip.com/itinerary/api/12808/lowestPrice?flightWay={config["flightWay"]}&dcity={config["placeTo"]}&acity={config["placeFrom"]}&direct=true&army=false'

    # get the price periodicly and alert through wechat
    targetPrice = config["targetPrice"]
    # histMin = 9999 # renew each month
    is_pm = True
    while True:
        r_goto = requests.get(url_goto)
        r_back = requests.get(url_back)
        if r_goto.status_code != 200 or r_goto.json()["status"] == 2 or r_back.status_code != 200 or r_back.json()["status"] == 2:
            pushMessage('机票信息获取失败', "### " + f'{time.strftime("%Y-%m-%d %H:%M")}', config["ftqq_SCKEY"])
        else:
            result_goto = r_goto.json()["data"]["oneWayPrice"][0]
            result_back = r_back.json()["data"]["oneWayPrice"][0]
            messageTitle, messageContent, minPrice = processData([result_goto, result_back])
            # histMin = min(minPrice, histMin)
            if minPrice <= 490:
                pushMessage(messageTitle, messageContent, config["ftqq_SCKEY"])
        print(f'{time.strftime("%Y-%m-%d %H:%M")}: 查询完毕')
        if is_pm:
            time.sleep((datetime.strptime("11:00:00", "%H:%M:%S") - datetime.today()).seconds)
            is_pm = False
        else:
            time.sleep((datetime.strptime("17:00:00", "%H:%M:%S") - datetime.today()).seconds)
            is_pm = True
