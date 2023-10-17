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

whitelist = ['BONDUSDT', 'LOOMUSDT', 'STPTUSDT', 'BETAUSDT', 'AKROUSDT', 'RUNEUSDT', 'BTCUSDT', 'ETHUSDT', 'RIFUSDT', 'DIAUSDT', 'XVSUSDT', 'BTSUSDT', 'LINKUSDT']
balances, tickets, info = [], [], []
balance = float(client.get_asset_balance(asset='USDT')['free'])
partOfBalance = 5.5
signalCounter = 0

info = client.futures_exchange_info()
    
def get_precision(symbol):
   for x in info['symbols']:
    if x['symbol'] == symbol:
        return x['quantityPrecision']

print(get_precision('BTCUSDT'))

def buy(Json):
    try:
        
        now = datetime.now()
        qty = partOfBalance / round(Json['prices'][-1], get_precision(Json['symbol']) - 1)
        order = client.create_order(
            symbol=Json['symbol'],
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_MARKET,
            quantity=qty
        )
        Ticket = {
            'symbol' : json['symbol'],
            'price' : json['prices'][-1],
            'qty' : partOfBalance / json['prices'][-1],
            'time' : now,
            'sold' : False,
            'status' : ''
        }
        tickets.append(Ticket)
    except Exception as E:
        print(E)

def sell(ticket):
    try:
        order = client.create_order(
            symbol = ticket['symbol'],
            side = Client.SIDE_SELL,
            type = Client.ORDER_TYPE_MARKET,
            quatity = ticket['qty'] * 0.999
        )
    except Exception as E:
        print(Exception)

def checkTicketsToSell(tickets, price, symbol):
    for ticket in tickets:
        if ticket['symbol'] == symbol:
            if ticket['price'] > price * 0.03:
                sell(ticket)
                ticket['sold'] = True
                ticket['status'] = 'gain'
            if  ticket['price'] < price * 0.03 :
                sell(ticket)
                ticket['sold'] = True
                ticket['status'] = 'loss'
            
Jsons = []
def makeCoinsJson(symbol):
    coinJson = {
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
        'buySignal' : [False, False, False] 
    }
    Jsons.append(coinJson)

def appendPrices(Json):
    coin = Json['symbol']
    price = float(tickers.loc[tickers['symbol'] == f'{coin}']['price'])
    Json['prices'].append(price)


def Rsis(json):
    diff = json['prices'][-2] - json['prices'][-1]
    if diff > 0:
        json['avg_gain'] += diff
        RS = json['avg_gain'] / (json['avg_loss'] * -1)
        RSI = 100 - 100 / (1 + RS)
        json['rsis'].append(RSI) 
    elif diff < 0:
        json['avg_loss'] += diff
        RS = json['avg_gain'] / (json['avg_loss'] * -1)
        RSI = 100 - 100 / (1 + RS) 
        json['rsis'].append(RSI)
    if len(json['rsis']) > 1:
        if (json['rsis'][-1] < 25 and json['rsis'][-1] > 20):
            json['buySignal'][0] = True
    
def Mcds(json):
    long_EMA = sum(json['prices'][:-26:-1]) / len(json['prices'][:-26:-1])
    short_EMA = sum(json['prices'][:-12:-1]) / len(json['prices'][:-12:-1])
    short_diff_EMA = sum(json['prices'][:-9:-1]) / len(json['prices'][:-9:-1])
    json['long_EMA'].append(long_EMA)
    json['short_EMA'].append(short_EMA)
    json['short_diff_EMA'].append(short_diff_EMA)
    MACD = round(json['short_EMA'][-1] - json['long_EMA'][-1], 3)
    signal = short_diff_EMA * (short_EMA - long_EMA)
    json['macds'].append(MACD)
    if len(json['macds']) > 10 and MACD - signal > -0.6 and MACD - signal < 0.6:
        json['buySignal'][1] = True
        
def Stochastic(json):
    priceLock = json['prices'][-1]
    minimum = min(json['prices'][:15])
    maximum = max(json['prices'][:15])
    Stoch = (priceLock - minimum) / (maximum - minimum) * 100
    json['stoch'].append(Stoch)
    if len(json['stoch']) > 10 and Stoch < 20:
        json['buySignal'][2] = True

def checkIndicators(json):
    global signalCounter
    if len(json['prices']) > 2:
        Rsis(json)
    if len(json['prices']) > 30:
        Mcds(json)
    if len(json['stoch']) > 15:
        Stochastic(json)
    for i in json['buySignal']:
        if i == True:
            signalCounter += 1
        if signalCounter >= 1:
            buy(json)
            signalCounter = 0
            json['buySignal'] = [False, False, False]

def makePlotBalance():
    now = datetime.now()
    plt.plot(*range(10), balances)
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


for i in range(200):
    print('Cycle number - ', i)
    tickers = client.get_all_tickers()
    tickers = pd.DataFrame(tickers)
    for Json in Jsons:
        appendPrices(Json)
        if len(Json['prices']) > 15: 
            checkIndicators(Json)
            checkTicketsToSell(tickets, Json['prices'][-1], Json['symbol'])

    time.sleep(20)

coinInfo = pd.DataFrame(Jsons)
ticketsInfo = pd.DataFrame(tickets)
makeStatistic(tickets)
coinInfo
tickets
