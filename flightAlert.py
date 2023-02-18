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

def processData(result, historyMin):
    priceDict = {}
    for idate, iprice in result.items():
        day = datetime.strptime(idate, "%Y%m%d")
        day_weekday = day.weekday() + 1
        if day_weekday >= 5: # skip Monday to Wednesday
            priceDict[day.strftime("%m-%d") + "(" + str(day_weekday) + ")"] = iprice

    minPrice = min(priceDict.values())
    dateWithMin = [x for x in priceDict if priceDict[x] == minPrice]

    historyMin = min(minPrice, historyMin)
    title = f"当前低价: {minPrice}, 历史最低: {historyMin}"
    content = "### " + " ".join(dateWithMin)
    content += "\n\n所有日期价格:"
    for idate, iprice in priceDict.items():
        content += "\n\n"
        content += idate + ": " + str(iprice)

    return title, content, minPrice

if __name__ == "__main__":
    # first import the json config file
    with open("config.json") as f:
        config = json.load(f)
    # assemble the request url
    baseUrl = "https://flights.ctrip.com/itinerary/api/12808/lowestPrice?"
    url = f'https://flights.ctrip.com/itinerary/api/12808/lowestPrice?flightWay={config["flightWay"]}&dcity={config["placeFrom"]}&acity={config["placeTo"]}&direct=true&army=false'

    # get the price periodicly and alert through wechat
    targetPrice = config["targetPrice"]
    histMin = 9999 # renew each month
    while True:
        r = requests.get(url)
        if r.status_code != 200 or r.json()["status"] == 2:
            pushMessage('机票信息获取失败', f'{time.strftime("%Y-%m-%d %H:%M")}', config["ftqq_SCKEY"])
        else:
            result = r.json()["data"]["oneWayPrice"][0]
            messageTitle, messageContent, minPrice = processData(result, histMin)
            histMin = min(minPrice, histMin)
            if minPrice <= targetPrice:
                pushMessage(messageTitle, messageContent, config["ftqq_SCKEY"])
        print(f'{time.strftime("%Y-%m-%d %H:%M")}：查询完毕')
        time.sleep(config["sleepTime"])
