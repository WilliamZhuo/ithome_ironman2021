from shioaji.data import Kbars
import pandas as pd
import shioaji
import matplotlib.pyplot as plt


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
df_kbars=getStockKbars(stockid='0050',start="2010-01-01",end="2021-09-02")
close=extractCol(df_kbars,col='Close')
dayclose=createDaySeries(close)
buy=maSignal(dayclose,periodLong=30,periodShort=5)

openprice=extractCol(df_kbars,col='Open')
dayopen=createDaySeries(openprice,mode='open')

ret,setting,bestbuy,bestretseries=optimizeMA(dayopen,dayclose)

#Buy and hold signal
allbuy=buy.copy()
for i in range(0,allbuy.size,1):
    allbuy[i]=True    
allret,allretseries=backtest_signal(dayopen,allbuy,spread=0.0000176)
#prefix product
allPrefixProd=prefixProd(allretseries)
#plot
plt.plot(allPrefixProd)

plt.plot(dayopen)

#ma signal prefix product
maPrefixProd=prefixProd(bestretseries)
#plot
plt.plot(maPrefixProd)

print("MDD hold:",calculatMDD(allPrefixProd))
print("MDD ma:",calculatMDD(maPrefixProd))

