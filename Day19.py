from shioaji.data import Kbars
import pandas as pd
import shioaji
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np
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

def getContractKbars(contract,start="2010-01-01",end="2021-09-02"):
    global api
    kbars = api.kbars(contract, start=start, end=end)
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
    highprice=extractCol(df_kbars,col='High')
    dayhigh=createDaySeries(highprice,mode='high')    
    lowprice=extractCol(df_kbars,col='Low')
    daylow=createDaySeries(lowprice,mode='low')    
    if(col=='Close'):
        return dayclose
    elif(col=='Open'):
        return dayopen
    elif(col=='High'):
        return dayhigh
    elif(col=='Low'):
        return daylow
    
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
    def create_PairForSeries_High(date,series):
        val=series[str(date)].max()
        return pd.Series({date:val})  
    def create_PairForSeries_Low(date,series):
        val=series[str(date)].min()
        return pd.Series({date:val})  
    
    def create_PairForSeries(date,series):
        if mode=='close':
            return create_PairForSeries_Close(date,series)
        elif mode=='open':
            return create_PairForSeries_Open(date,series)
        elif mode=='high':
            return create_PairForSeries_High(date,series)
        elif mode=='low':
            return create_PairForSeries_Low(date,series)
            
    dayclose=create_PairForSeries(date_begin,series)
    date_begin += delta
    while date_begin <= date_end:
        try:
            append=create_PairForSeries(date_begin,series)
            dayclose=dayclose.append(append)
        except:
            pass
        date_begin += delta
    return dayclose.dropna()

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

def backtest_signal(dayopen,signal,spread=0.0000176,sizing=1.0):
    buy=signal.astype(float)
    position=buy.shift(1)
    position[0]=0.0
    
    ret_series=pd.Series()    
    for i in range(0,position.size,1):
        try:
            temp=period_profit(dayopen,buybegin=i,buyend=i+1)
            profit=temp-1.0
            cost=0
            #單邊交易成本,單位是百分比
            try:
                #buy->sell or sell->buy
                positionchange=abs(position[i]-position[i-1])
                if(positionchange>0):
                    #spread=0.0000176  #價差,各商品不同,指數etf中最高的是006204 0.006
                    tax=0.0015        #交易稅
                    commission=0.001425 #手續費, **
                    cost=tax+commission
                    cost=cost*positionchange
            except:
                pass           
            
            ret=1.0+profit*position[i]*sizing+cost*sizing
            
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
    
def optimizeGeneral(dayopen,buy,parameters,args):
    bestret=args['bestret']
    retStrategy,ret_series=backtest_signal(dayopen,buy)
    if retStrategy>bestret:
        print("return:",retStrategy)
        print("bestparameter:",parameters)        
        args['bestparameter']=parameters
        args['bestret']=retStrategy
        args['bestbuy']=buy
        args['bestretseries']=ret_series
        
class strategy_SAR:
    argsDefault={'acceleration':0.02,'maximum':0.2}
    #only int or float is supported right now
    def __init_(self):
        pass
    def createsignal(self,kbars_daily,parameters):
        dayhigh=kbars_daily['High']        
        daylow=kbars_daily['Low'] 
        dayclose=kbars_daily['Close']
        acceleration=parameters['acceleration']
        maximum=parameters['maximum']
        real = talib.SAR(dayhigh, daylow, acceleration=acceleration, maximum=maximum)
        return dayclose>real
    
    def bodyfor_optimize(self,args,previouslist):
        #args:kbars_daily + othre data
        #previouslist:[periodLong,periodShort]
        kbars_daily=args['kbars_daily']
        dayclose=kbars_daily['Close']
        dayopen=kbars_daily['Open']
        bestret=args['bestret']
        dayhigh=kbars_daily['High']
        daylow=kbars_daily['Low']
        
        #客製化
        acceleration=previouslist[0]
        maximum=previouslist[1]
        parameters={'acceleration':acceleration,'maximum':maximum}
        
        buy=self.createsignal(kbars_daily,parameters)
        #通用
        optimizeGeneral(dayopen,buy,parameters,args)

        
class strategy_MA:
    argsDefault={'periodLong':30,'periodShort':5}
    #argsRange={'acceleration':np.arange(0.02,0.2,0.02),'maximum':np.arange(0.2,0.2,0.2)}
    #only int or float is supported right now
    def __init_(self):
        pass
    def createsignal(self,kbars_daily,parameters):
        dayhigh=kbars_daily['High']        
        daylow=kbars_daily['Low'] 
        dayclose=kbars_daily['Close']
        periodLong=parameters['periodLong']
        periodShort=parameters['periodShort']
        signal=maSignal(dayclose,periodLong=periodLong,periodShort=periodShort)
        return signal
    
    def bodyfor_optimize(self,args,previouslist):
        #args:kbars_daily + othre data
        #previouslist:[periodLong,periodShort]
        kbars_daily=args['kbars_daily']
        dayclose=kbars_daily['Close']
        dayopen=kbars_daily['Open']
        bestret=args['bestret']
        dayhigh=kbars_daily['High']
        daylow=kbars_daily['Low']
        
        #客製化
        periodLong=previouslist[0]
        periodShort=previouslist[1]
        if periodShort>=periodLong:
            return
        parameters={'periodLong':periodLong,'periodShort':periodShort}
        buy=self.createsignal(kbars_daily,parameters)

        #通用
        optimizeGeneral(dayopen,buy,parameters,args)


class strategy_Grid:
    argsDefault={'BiasUpper':2,\
                 'UpperPosition':0.3,\
                 'BiasLower':0.5,\
                 'LowerPosition':0.7,\
                 'BiasPeriod':20}
    #only int or float is supported right now
    def __init_(self):
        pass
    def createsignal(self,kbars_daily,parameters):
        dayhigh=kbars_daily['High']        
        daylow =kbars_daily['Low'] 
        dayclose=kbars_daily['Close']
        
        BiasUpper=parameters['BiasUpper']
        UpperPosition=parameters['UpperPosition']
        BiasLower=parameters['BiasLower']
        LowerPosition=parameters['LowerPosition']
        BiasPeriod=parameters['BiasPeriod']
        Bias=dayclose/dayclose.rolling(window=BiasPeriod).mean()
        Bias=Bias.fillna(method='bfill')
        
        positiondiff=UpperPosition-LowerPosition
        biasdiff=BiasUpper-BiasLower
        position=LowerPosition+(Bias-BiasLower)*positiondiff/biasdiff
        position[Bias<=BiasLower]=LowerPosition
        position[Bias>=BiasUpper]=UpperPosition
        return position

    
    def bodyfor_optimize(self,args,previouslist):
        #args:kbars_daily + othre data
        #previouslist:[periodLong,periodShort]
        kbars_daily=args['kbars_daily']
        dayclose=kbars_daily['Close']
        dayopen=kbars_daily['Open']
        bestret=args['bestret']
        dayhigh=kbars_daily['High']
        daylow=kbars_daily['Low']
        
        #客製化
        BiasUpper=previouslist[0]
        UpperPosition=previouslist[1]
        BiasLower=previouslist[2]
        LowerPosition=previouslist[3]
        BiasPeriod=previouslist[4]
        if BiasLower>=BiasUpper:
            return
        if LowerPosition<=UpperPosition:
            return
        parameters={'BiasUpper':BiasUpper,\
                    'UpperPosition':UpperPosition,\
                    'BiasLower':BiasLower,\
                    'LowerPosition':LowerPosition,\
                    'BiasPeriod':BiasPeriod,\
                    }
        buy=self.createsignal(kbars_daily,parameters)

        #通用
        optimizeGeneral(dayopen,buy,parameters,args)


    
def recursiveloop(thelist,func,args,previouslist= list(),idx=0):
    if(idx==len(thelist)):
        #action here
        func(args,previouslist)
    else:
        for i in thelist[idx]:
            arg=previouslist.copy()
            arg.append(i)
            recursiveloop(thelist,func,args,previouslist=arg,idx=idx+1)
    
def strategy_optimize(kbars_daily,strategy_obj,rangelist):
    bestret=0
    bestparameter=strategy_obj.argsDefault
    bestbuy=[]
    bestretseries=[]
    args_pack={'kbars_daily':kbars_daily\
              ,'bestparameter':bestparameter\
              ,'bestret':bestret\
              ,'bestbuy':bestbuy\
              ,'bestretseries':bestretseries\
        }
    recursiveloop(rangelist,strategy_obj.bodyfor_optimize,args_pack)
    bestret=args_pack['bestret']
    bestparameter=args_pack['bestparameter']
    bestbuy=args_pack['bestbuy']
    bestretseries=args_pack['bestretseries']
    return bestret,bestparameter,bestbuy,bestretseries

DF_FUTURE_SYMBOL=pd.read_csv('SYMBOL.csv')  
def createFutureNameLookup():
    v=vars(api.Contracts.Futures)
    l=list(v.keys())
    reference={}
    for i in range(0,len(l),1):
        if(len(l[i])>3):
            pass
        else:
            name=DF_FUTURE_SYMBOL.loc[DF_FUTURE_SYMBOL['symbol'] == l[i]]['name'].item()
            reference[l[i]]=name
    return reference


shioajiLogin(simulation=False)


TW_close=getStockDailyPrice(stockid='006208',start="2010-01-01",end="2021-09-02",col='Open')
TW_open=getStockDailyPrice(stockid='006208',start="2010-01-01",end="2021-09-02",col='Close')
TW_high=getStockDailyPrice(stockid='006208',start="2010-01-01",end="2021-09-02",col='High')
TW_low=getStockDailyPrice(stockid='006208',start="2010-01-01",end="2021-09-02",col='Low')

kbars_daily_TW = pd.DataFrame(\
    {'ts':TW_close.index\
    ,'Close':TW_close\
    ,'Open':TW_open\
    ,'High':TW_high\
    ,'Low':TW_low}) 


#以下是搜尋範圍，但直接這樣做最佳化太久
#所以分三次最佳化,第一次 BiasUpperBiasLower,第二次 UpperPosition和LowerPosition
#第三次BiasPeriod
'''
list_Grid_range=\
    [np.arange(1.0,2.1,0.1)\
     ,np.arange(0.0,0.5,0.1)\
     ,np.arange(0.1,1.0,0.1)\
     ,np.arange(0.5,1.0,0.1)\
     ,np.arange(5,60,5)\
     ]
'''
#預設值
BiasUpper=2.0
UpperPosition=0.3
BiasLower=0.5
LowerPosition=0.7
BiasPeriod=20

list_Grid_range=\
    [np.arange(1.0,2.1,0.1)\
     ,np.arange(UpperPosition,UpperPosition+0.1,0.1)\
     ,np.arange(0.1,1.0,0.1)\
     ,np.arange(LowerPosition,LowerPosition+0.1,0.1)\
     ,np.arange(BiasPeriod,BiasPeriod+5,5)\
     ]
Grid=strategy_Grid()
retGrid=strategy_optimize(kbars_daily_TW,Grid,list_Grid_range)

BiasUpper=retGrid[1]['BiasUpper']
UpperPosition=retGrid[1]['UpperPosition']
BiasLower=retGrid[1]['BiasLower']
LowerPosition=retGrid[1]['LowerPosition']
BiasPeriod=retGrid[1]['BiasPeriod']

list_Grid_range=\
    [np.arange(BiasUpper,BiasUpper+0.1,0.1)\
     ,np.arange(0.1,0.5,0.1)\
     ,np.arange(BiasLower,BiasLower+0.1,0.1)\
     ,np.arange(0.5,1.0,0.1)\
     ,np.arange(BiasPeriod,BiasPeriod+5,5)\
     ]
retGrid=strategy_optimize(kbars_daily_TW,Grid,list_Grid_range)

BiasUpper=retGrid[1]['BiasUpper']
UpperPosition=retGrid[1]['UpperPosition']
BiasLower=retGrid[1]['BiasLower']
LowerPosition=retGrid[1]['LowerPosition']
BiasPeriod=retGrid[1]['BiasPeriod']

list_Grid_range=\
    [np.arange(BiasUpper,BiasUpper+0.1,0.1)\
     ,np.arange(UpperPosition,UpperPosition+0.1,0.1)\
     ,np.arange(BiasLower,BiasLower+0.1,0.1)\
     ,np.arange(LowerPosition,LowerPosition+0.1,0.1)\
     ,np.arange(5,60,5)\
     ]
        
retGrid=strategy_optimize(kbars_daily_TW,Grid,list_Grid_range)


retseriesProfit=retGrid[3]
prefixProfit=prefixProd(retseriesProfit)
plt.plot(prefixProfit,color='green')

position=retGrid[2]
plt.plot(position,color='red')
