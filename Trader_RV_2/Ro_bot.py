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
def Rsis(CoinInfo):
    diff = CoinInfo['prices'][-2] - CoinInfo['prices'][-1]
    EMAUp = sum(CoinInfo) / len(CoinInfo)
    EMADown = sum(CoinInfo) / len(CoinInfo)
    if diff > 0:
        CoinInfo['avg_gain'].append(diff)
        EMAUp = sum(CoinInfo['avg_gain']) / len(CoinInfo['avg_gain'])
        RS = CoinInfo['avg_gain'] / (CoinInfo['avg_loss'])
        RSI = 100 - 100 / (1 + RS)
        CoinInfo['rsis'].append(RSI) 
    elif diff < 0:
        CoinInfo['avg_loss'].append(diff)
        EMADown = sum(CoinInfo['avg_loss']) / len(CoinInfo['avg_loss'])
        if EMADown < 0:
            EMADown = EMADown * -1
        RS = EMAUp / EMADown
        RSI = 100 - 100 / (1 + RS) 
        CoinInfo['rsis'].append(RSI)
    if len(CoinInfo['rsis']) > 1:
        if (CoinInfo['rsis'][-1] < 30 and CoinInfo['rsis'][-1] > 20):
            CoinInfo['buySignal'][0] = True
    
def Mcds(CoinInfo):
    long_EMA = sum(CoinInfo['prices'][:-26:-1]) / len(CoinInfo['prices'][:-26:-1])
    short_EMA = sum(CoinInfo['prices'][:-12:-1]) / len(CoinInfo['prices'][:-12:-1])
    short_diff_EMA = sum(CoinInfo['prices'][:-9:-1]) / len(CoinInfo['prices'][:-9:-1])
    CoinInfo['long_EMA'].append(long_EMA)
    CoinInfo['short_EMA'].append(short_EMA)
    CoinInfo['short_diff_EMA'].append(short_diff_EMA)
    MACD = round(CoinInfo['short_EMA'][-1] - CoinInfo['long_EMA'][-1], 3)
    signal = short_diff_EMA * (short_EMA - long_EMA)
    CoinInfo['macds'].append(MACD)
    if len(CoinInfo['macds']) > 10 and MACD - signal > -0.6 and MACD - signal < 0.6:
        CoinInfo['buySignal'][1] = True
        
def Stochastic(CoinInfo):
    priceLock = CoinInfo['prices'][-1]
    minimum = min(CoinInfo['prices'][:15])
    maximum = max(CoinInfo['prices'][:15])
    Stoch = (priceLock - minimum) / (maximum - minimum) * 100
    CoinInfo['stoch'].append(Stoch)
    if len(CoinInfo['stoch']) > 10 and Stoch < 20:
        CoinInfo['buySignal'][2] = True

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
        print(x)
        print(precision)
        print(coinInfo['symbol'])


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
        'avg_gain' : [],
        'avg_loss' : [],
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
    for coinInfo in coinInfos:
        appendPrices(coinInfo)
        # balance = float(client.get_asset_balance(asset='USDT')['free'])
        if len(coinInfo['prices']) > 10:
            checkIndicators(coinInfo)
            checkTicketsToSell(tickets, coinInfo['prices'][-1], coinInfo['symbol'][-1])
        time.sleep(5)
    makeStatistic(tickets)
for ticket in tickets:
    sell(ticket)

df = pd.DataFrame(coinInfos)
df
