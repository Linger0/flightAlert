import json
import requests
import time
import math
from datetime import datetime

def pushMessage(messagetitle, messagecontent, tokens):
    sendData = {'title': messagetitle, 'content': messagecontent}
    for tok in tokens:
        sendUrl = f'https://sctapi.ftqq.com/{tok}.send'
        requests.post(sendUrl, data=sendData)

def printMessage(messagetitle, messagecontent, *skip):
    print(messagetitle)
    print(messagecontent)

# Calculate the price difference between 2 days.
def monitorCertainDates(results, priceStep, datesTogo, datesBack, history, cities):
    resLeav, resBack = results
    cfrom, cto = cities
    histMinLeav = history['minLeav']
    histLeav = history['prevLeav']
    histMinBack = history['minBack']
    histBack = history['prevBack']
    toSend = False
    resLeavDates = {}
    resBackDates = {}
    for date in datesTogo:
        resLeavDates[date] = resLeav[date]
    for date in datesBack:
        resBackDates[date] = resBack[date]

    minLeavPrice = min(resLeavDates.values())
    if abs(minLeavPrice - histLeav) >= priceStep:
        history['prevLeav'] = minLeavPrice
        toSend = True

    minBackPrice = min(resBackDates.values())
    if abs(minBackPrice - histBack) >= priceStep:
        history['prevBack'] = minBackPrice
        toSend = True

    histMinLeav = min(histMinLeav, minLeavPrice)
    histMinBack = min(histMinBack, minBackPrice)
    history['minLeav'] = histMinLeav
    history['minBack'] = histMinBack

    title = f' Current price to {cto}: {minLeavPrice} ↔ {minBackPrice}'
    content = f'*{cfrom}–{cto}:*\n\n'
    for date, price in resLeavDates.items():
        content += '**' + date[4:6] + '-' + date[6:8] + f': {price}**\n\n'
    content += f'History lowest: {histMinLeav}\n\n'
    content += '---\n\n'
    content += f'*{cto}–{cfrom}:*\n\n'
    for date, price in resBackDates.items():
        content += '**' + date[4:6] + '-' + date[6:8] + f': {price}**\n\n'
    content += f'History lowest: {histMinBack}'

    return title, content, toSend

# Obtain the lowest price for departure and return trip.
def monitor2MonthWeekend(results, targetPrice, **skip):
    resLeav, resBack = results
    priceLeavDict = {}
    priceBackDict = {}
    for date in resLeav:
        day = datetime.strptime(date, "%Y%m%d")
        deltaDay = day - datetime.today()
        if deltaDay.days >= 60:
            break

        weekday = day.weekday() + 1
        if weekday >= 4: # skip Monday to Wednesday
            priceLeavDict[day.strftime("%m-%d") + r"(" + str(weekday) + r")"] = resLeav[date]
            priceBackDict[day.strftime("%m-%d") + r"(" + str(weekday) + r")"] = resBack[date]

    minLeavPrice = min(priceLeavDict.values())
    dateMinLeav = [x for x in priceLeavDict if priceLeavDict[x] == minLeavPrice]
    minBackPrice = min(priceBackDict.values())
    dateMinBack = [x for x in priceBackDict if priceBackDict[x] == minBackPrice]
    maxMinPrice = max(minLeavPrice, minBackPrice)

    title = f' Lowest price: {minLeavPrice} (SHA–BJS) ↔ {minBackPrice} (BJS-SHA)'
    content = f"### {minLeavPrice} (SHA–BJS): " + " ".join(dateMinLeav)
    content += f"\n\n### {minBackPrice} (BJS-SHA): " + " ".join(dateMinBack)
    content += "\n\nPrice list:\n\n&emsp;&emsp;&emsp;&emsp;SHA–BJS&ensp;BJS–SHA\n\n---"
    for date in priceLeavDict:
        content += "\n\n"
        weekday = date[6]
        content += date + ":&emsp;" \
            + ("**" if priceLeavDict[date] <= maxMinPrice else "") \
            + str(priceLeavDict[date]) \
            + ("**" if priceLeavDict[date] <= maxMinPrice else "") \
            + "&emsp;&emsp;&emsp;" \
            + ("**" if priceBackDict[date] <= maxMinPrice else "") \
            + str(priceBackDict[date]) \
            + ("**" if priceBackDict[date] <= maxMinPrice else "")
        if weekday == "7":
            content += "\n\n---"

    toSend = maxMinPrice <= targetPrice
    return title, content, toSend

if __name__ == "__main__":
    test = False
    mode = 1

    baseUrl = "https://flights.ctrip.com/itinerary/api/12808/lowestPrice?"
    # first import the json config file
    with open("config.json") as f:
        config = json.load(f)
    # assemble the request url
    urlLeav = f'https://flights.ctrip.com/itinerary/api/12808/lowestPrice?flightWay={config["flightWay"]}&dcity={config["placeFrom"]}&acity={config["placeTo"]}&direct=true&army=false'
    urlBack = f'https://flights.ctrip.com/itinerary/api/12808/lowestPrice?flightWay={config["flightWay"]}&dcity={config["placeTo"]}&acity={config["placeFrom"]}&direct=true&army=false'

    # get the price periodicly and alert through wechat
    targetPrice = config["targetPrice"]
    priceStep = config["priceStep"]
    history = {"minLeav": 9999, "prevLeav": 0, "minBack": 9999, "prevBack": 0}
    releaseMessage = printMessage if test else pushMessage
    while True:
        # request the url
        reqLeav = requests.get(urlLeav)
        reqBack = requests.get(urlBack)

        if reqLeav.status_code != 200 or reqLeav.json()["status"] == 2 or reqBack.status_code != 200 or reqBack.json()["status"] == 2:
            releaseMessage('Failed to retrieve flight ticket information.', "### " + f'{time.strftime("%Y-%m-%d %H:%M")}', config["ftqq_SCKEY"])
        else:
            # analyse the results
            resLeav = reqLeav.json()["data"]["oneWayPrice"][0]
            resBack = reqBack.json()["data"]["oneWayPrice"][0]
            if mode == 1:
                messageTitle, messageContent, toSend = monitorCertainDates(
                    [resLeav, resBack], priceStep, config['dateToGo'], config['dateBack'], history, [config['placeFrom'], config['placeTo']])
            elif mode == 2:
                messageTitle, messageContent, toSend = monitor2MonthWeekend([resLeav, resBack], targetPrice=targetPrice)
            # send message
            if toSend:
                releaseMessage(messageTitle, messageContent, config["ftqq_SCKEY"])

        print(f'{time.strftime("%Y-%m-%d %H:%M")} finished. Waiting for tomorrow.')

        if not test:
            time.sleep((datetime.strptime("17:00:00", "%H:%M:%S") - datetime.now()).seconds)
        else:
            break
