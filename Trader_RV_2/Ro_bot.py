import pandas as pd
from binance.client import Client
import re
import time
import json
from datetime import datetime
import matplotlib as plt
api_key = 'z7Ltgm7gB1OBsvRiSPCuYOIq7CHMXEVT1ch4vnGuuxZ4I9kaKc7gwLbmd6n3HBJ2'
api_secret = '3h3ylP3VtH6Rtvm83aoHrcI8erMjZfNeX6MAgRGnSHL1srkvu2WcJlUnH1fq59LX'

client = Client(api_key, api_secret)

tickers = client.get_all_tickers()
tickers = pd.DataFrame(tickers)
whitelist = ['ETHUSDT', 'SOLUSDT', 'DOGEUSDT', 'LTCUSDT', 'SHIBUSDT', 'PLAUSDT', 'ONTUSDT', 'FARMUSDT', 'HARDUSDT', 'CHESSUSDT']
balances, tickets, info = [], [], []
balance = float(client.get_asset_balance(asset='USDT')['free'])
partOfBalance = 10
signalCounter = 0
info = client.futures_exchange_info()
coinInfos = []

def get_precision(symbol):
   for x in info['symbols']:
    if x['symbol'] == symbol:
        return x['quantityPrecision']
def Rsis(CoindInfo):
    diff = CoindInfo['prices'][-2] - CoindInfo['prices'][-1]
    if diff > 0:
        CoindInfo['avg_gain'] += diff
        RS = CoindInfo['avg_gain'] / (CoindInfo['avg_loss'] * -1)
        RSI = 100 - 100 / (1 + RS)
        CoindInfo['rsis'].append(RSI) 
    elif diff < 0:
        CoindInfo['avg_loss'] += diff
        RS = CoindInfo['avg_gain'] / (CoindInfo['avg_loss'] * -1)
        RSI = 100 - 100 / (1 + RS) 
        CoindInfo['rsis'].append(RSI)
    if len(CoindInfo['rsis']) > 1:
        if (CoindInfo['rsis'][-1] < 30 and CoindInfo['rsis'][-1] > 20):
            CoindInfo['buySignal'][0] = True
    
def Mcds(CoindInfo):
    long_EMA = sum(CoindInfo['prices'][:-26:-1]) / len(CoindInfo['prices'][:-26:-1])
    short_EMA = sum(CoindInfo['prices'][:-12:-1]) / len(CoindInfo['prices'][:-12:-1])
    short_diff_EMA = sum(CoindInfo['prices'][:-9:-1]) / len(CoindInfo['prices'][:-9:-1])
    CoindInfo['long_EMA'].append(long_EMA)
    CoindInfo['short_EMA'].append(short_EMA)
    CoindInfo['short_diff_EMA'].append(short_diff_EMA)
    MACD = round(CoindInfo['short_EMA'][-1] - CoindInfo['long_EMA'][-1], 3)
    signal = short_diff_EMA * (short_EMA - long_EMA)
    CoindInfo['macds'].append(MACD)
    if len(CoindInfo['macds']) > 10 and MACD - signal > -0.6 and MACD - signal < 0.6:
        CoindInfo['buySignal'][1] = True
        
def Stochastic(CoindInfo):
    priceLock = CoindInfo['prices'][-1]
    minimum = min(CoindInfo['prices'][:15])
    maximum = max(CoindInfo['prices'][:15])
    Stoch = (priceLock - minimum) / (maximum - minimum) * 100
    CoindInfo['stoch'].append(Stoch)
    if len(CoindInfo['stoch']) > 10 and Stoch < 20:
        CoindInfo['buySignal'][2] = True
def buy(coinInfo):
    try:
        now = datetime.now()
        precision = get_precision(coinInfo['symbol'])
        if precision == 0 or precision == None:
            precision = 1
        else:
            precision = int(precision)
        x = round(coinInfo['prices'][-1], precision)
        if x > 0:
            qty = partOfBalance / x
            qty = round(qty, precision)
            print(qty)
            order = client.create_order(
                symbol=coinInfo['symbol'],
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=qty
            )
            print("Bouth ", coinInfo['symbol'], ' price ', coinInfo['prices'][-1])
            Ticket = {
                'symbol' : coinInfo['symbol'],
                'price' : coinInfo['prices'][-1],
                'qty' : qty,
                'time' : now,
                'sold' : False,
                'status' : ''
            }
            tickets.append(Ticket)
    except Exception as E:
        print(E)


def sell(ticket):
    try:
        order = client.order_market_sell(
            symbol=ticket['symbol'],
            quantity=ticket['qty']
            )
        print('Sold ', ticket['symbol'])
        ticket['sold'] = True
    except Exception as E:
        print(E)
def appendPrices(coinInfo):
    coin = coinInfo['symbol']
    price = float(tickers.loc[tickers['symbol'] == f'{coin}']['price'])
    coinInfo['prices'].append(price)
def makeCoinsJson(symbol):
    precision = get_precision(symbol)
    if precision == 0 or precision == None:
        precision = 1
    else:
        precision = int(precision)

    coinInfo = {
        'symbol' : symbol,
        'prices' : [],
        'avg_gain' : 1,
        'avg_loss' : 1,
        'rsis' : [],
        'macds' : [],
        'long_EMA' : [],
        'short_EMA' : [],
        'short_diff_EMA' : [],
        'stoch' : [],
        'buySignal' : [False, False, False],
        'precision' : precision
    }
    coinInfos.append(coinInfo)
def checkIndicators(coinInfo):
    global signalCounter
    if len(coinInfo['prices']) > 2:
        Rsis(coinInfo)
    if len(coinInfo['prices']) > 30:
        Mcds(coinInfo)
    if len(coinInfo['prices']) > 15:
        Stochastic(coinInfo)
    for i in coinInfo['buySignal']:
        if i == True:
            signalCounter += 1
        if signalCounter >= 2:
            buy(coinInfo)
            signalCounter = 0
            coinInfo['buySignal'] = [False, False, False]            
def makePlotBalance():
    now = datetime.now()
    plt.plot(*range(len(balances)), balances)
    plt.savefig('report.png')
def makeStatistic(tickets):
    counterLoss = 0
    counterGain = 0
    for i in tickets:
        if i['status'] == 'loss':
            counterLoss += 1
        elif i['status'] == 'gain':
            counterGain += 1
        statistic = counterGain / counterLoss * 100
        print('Statistic - ', statistic)
    
for coin in whitelist:
    makeCoinsJson(coin)
def checkTicketsToSell(tickets, price, symbol):
    for ticket in tickets:
        if ticket['symbol'] == symbol:
            print('We waiting ', ticket['price'] + ticket['price'] * 0.005)
            if price > ticket['price'] + ticket['price'] * 0.005:
                sell(ticket)
                ticket['status'] = 'gain'
            elif price < ticket['price'] - ticket['price'] * 0.01:
                sell(ticket)
                ticket['status'] = 'loss'

for i in range(1000):
    try:
        for coinInfo in coinInfos:
            appendPrices(coinInfo)
            # balance = float(client.get_asset_balance(asset='USDT')['free'])
            if len(coinInfo['prices']) > 10:
                checkIndicators(coinInfo)
                checkTicketsToSell(tickets, coinInfo['prices'][-1], coinInfo['symbol'][-1])
            time.sleep(5)
        makeStatistic(tickets)
    except Exception as E:
        print(E)
for ticket in tickets:
    sell(ticket)

df = pd.DataFrame(coinInfos)
df
