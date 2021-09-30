from shioaji.data import Kbars
import pandas as pd
import shioaji
import matplotlib.pyplot as plt
import yfinance as yf
ratio_tradingcost=2
api=0
def shioajiLogin(simulation=False):
    global api
    api = shioaji.Shioaji(simulation=simulation)
    person_id=''#你的身分證字號
    passwd=''#你的永豐證券登入密碼
    if(person_id==''):
        person_id=input("Please input ID:\n")
    if(passwd==''):
        passwd=input("Please input PASSWORD:\n")
    api.login(
        person_id=person_id, 
        passwd=passwd, 
        contracts_cb=lambda security_type: print(f"{repr(security_type)} fetch done.")
    )
def getStockKbars(stockid='0050',start="2010-01-01",end="2021-09-02"):
    global api
    kbars = api.kbars(api.Contracts.Stocks[stockid], start=start, end=end)
    df = pd.DataFrame({**kbars})
    df.ts = pd.to_datetime(df.ts)
    return df

def getStockDailyPrice(stockid='0050',start="2010-01-01",end="2021-09-02",col='Close'):
    df_kbars=getStockKbars(\
            stockid=stockid\
            ,start=start\
            ,end=end)
    close=extractCol(df_kbars,col='Close')
    dayclose=createDaySeries(close)
    openprice=extractCol(df_kbars,col='Open')
    dayopen=createDaySeries(openprice,mode='open')    
    if(col=='Close'):
        return dayclose
    elif(col=='Open'):
        return dayopen
    
def extractCol(df_kbars,col='Close'):
    series=df_kbars[col]
    series.index=df_kbars.ts
    return series

def createDaySeries(series,mode='close'):
    import datetime
    date_begin=series.index[0].date()
    date_end=series.index[-1].date()
    delta = datetime.timedelta(days=1)
    
    def create_PairForSeries_Close(date,series):
        val=series[str(date)][-1]
        return pd.Series({date:val})  
    def create_PairForSeries_Open(date,series):
        val=series[str(date)][0]
        return pd.Series({date:val})  
    
    def create_PairForSeries(date,series):
        if mode=='close':
            return create_PairForSeries_Close(date,series)
        elif mode=='open':
            return create_PairForSeries_Open(date,series)
            
    dayclose=create_PairForSeries(date_begin,series)
    date_begin += delta
    while date_begin <= date_end:
        try:
            append=create_PairForSeries(date_begin,series)
            dayclose=dayclose.append(append)
        except:
            pass
        date_begin += delta
    return dayclose

import talib
def maSignal(close,periodLong=30,periodShort=5):
    maLong = talib.SMA(close,timeperiod=periodLong)
    maShort = talib.SMA(close,timeperiod=periodShort)
    diff=maShort-maLong
    #diff=diff.dropna() #均線最前面幾天會是Nan,所以要用dropna去除掉
    buy=diff>0
    return buy


def period_profit(openprice,buybegin=0,buyend=10):
    if(openprice[buybegin]==0):
        print('div0')
    return openprice[buyend]/openprice[buybegin]

def backtest_signal(dayopen,buy,spread=0.0000176):
    position=buy.shift(1)
    position[0]=False
    
    ret_series=pd.Series()    
    for i in range(0,position.size,1):
        try:
            if(position[i]==True):
                ret=period_profit(dayopen,buybegin=i,buyend=i+1)
            else:
                ret=1.0
                
            #單邊交易成本,單位是百分比
            try:
                #buy->sell or sell->buy
                if(abs(position[i]-position[i-1])>0):
                    #spread=0.0000176  #價差,各商品不同,指數etf中最高的是006204 0.006
                    tax=0.0015        #交易稅
                    commission=0.001425 #手續費, **
                    ret=ret*(1.0-spread-tax-commission)
            except:
                pass            
            
            thepair=pd.Series({i:ret})
            ret_series=ret_series.append(thepair)     
            
        except:
             pass
            #print('failat:',str(i))
            
    retStrategy=ret_series.to_numpy().prod()    
    #NOTE:最後一天的報酬率還沒出來，要等隔天的開盤價出來才會知道
    return retStrategy,ret_series

def optimizeMA(dayopen,dayclose,rangeLong=range(2,100,1),rangeShort=range(2,100,1)):
    bestret=0
    best_period_short=5
    best_period_long=30
    bestbuy=[]
    bestretseries=[]
    for periodLong in rangeLong:
        for periodShort in rangeShort:
            if periodShort>=periodLong:
                continue
            buy=maSignal(dayclose,periodLong=periodLong,periodShort=periodShort)
            retStrategy,ret_series=backtest_signal(dayopen,buy)
            if retStrategy>bestret:
                print("return:",retStrategy)
                print("periodLong:",periodLong)
                print("periodShort:",periodShort)
                bestret=retStrategy
                best_period_long=periodLong
                best_period_short=periodShort
                bestbuy=buy
                bestretseries=ret_series
    return bestret,(best_period_long,best_period_short),bestbuy,bestretseries

def prefixProd(retseries):
    clone=retseries.copy()
    prod=1
    for i in range(0,retseries.size,1):
        prod=prod*retseries[i]
        clone[i]=prod
    return clone

def calculatMDD(prefixProdSeries):
    maxval=prefixProdSeries[0]
    MDD=0
    for i in range(0,prefixProdSeries.size,1):
        maxval=max(prefixProdSeries[i],maxval)
        temp=1.0-prefixProdSeries[i]/maxval
        if(temp>MDD):
            MDD=temp
    return MDD

shioajiLogin(simulation=False)
dayclose0050=getStockDailyPrice(stockid='0050',start="2010-01-01",end="2021-09-02",col='Open')
dayopen0050=getStockDailyPrice(stockid='0050',start="2010-01-01",end="2021-09-02",col='Close')
dayclose0051=getStockDailyPrice(stockid='0051',start="2010-01-01",end="2021-09-02",col='Open')
dayopen0051=getStockDailyPrice(stockid='0051',start="2010-01-01",end="2021-09-02",col='Close')

import yfinance as yf

#0050
tw0050 = yf.Ticker("0050.tw")
hist = tw0050.history(period="10y")
tw0050_open=hist['Open']
tw0050_close=hist['Close']
after=tw0050_open.index[tw0050_open.size-dayopen0050.size]
tw0050_open=tw0050_open.truncate(after=after)
after=tw0050_close.index[tw0050_close.size-dayclose0050.size]
tw0050_close=tw0050_close.truncate(after=after)

# 0051
tw0051 = yf.Ticker("0051.tw")
hist = tw0051.history(period="10y")
tw0051_open=hist['Open']
tw0051_close=hist['Close']
after=tw0051_open.index[tw0051_open.size-dayopen0051.size]
tw0051_open=tw0051_open.truncate(after=after)
after=tw0051_close.index[tw0051_close.size-dayclose0051.size]
tw0051_close=tw0051_close.truncate(after=after)

open_div=tw0050_open/tw0051_open
close_div=tw0050_close/tw0051_close


#有兩天資料是0，會有錯誤，所以要把它們移除掉
ind_open=open_div==0
ind_close=close_div==0
open_div[ind_open + ind_close]=float("NaN")
close_div[ind_open + ind_close]=float("NaN")
ind_open=open_div==float("inf")   #a/0
ind_close=close_div==float("inf") #a/0
open_div[ind_open + ind_close]=float("NaN")
close_div[ind_open + ind_close]=float("NaN")
open_div=open_div.dropna()
close_div=close_div.dropna()

#最佳化
retYF,settingYF,bestbuyYF,bestretseriesYF\
    =optimizeMA(open_div\
                ,close_div\
                ,rangeLong=range(2,100,2)\
                ,rangeShort=range(2,100,2))


#用2019以後的資料測試
buy0050=maSignal(dayclose0050/dayclose0051,periodLong=settingYF[0],periodShort=settingYF[1])
buy0051=~buy0050
allret0050,allretseries0050=backtest_signal(dayopen0050,buy0050,spread=0.0000176)
allret0051,allretseries0051=backtest_signal(dayopen0051,buy0051,spread=0.0000176)
allretseries=allretseries0050*allretseries0051
allret=allret0050*allret0051
maPrefixProd=prefixProd(allretseries)
maMDD=calculatMDD(maPrefixProd)
print('allret:',allret)
print('maMDD:',maMDD)

plt.plot(maPrefixProd)
