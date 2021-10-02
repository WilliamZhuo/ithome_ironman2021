from shioaji.data import Kbars
import pandas as pd
import shioaji
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np
api=0
person_id=0
passwd=0
CA_passwd=0
def shioajiLogin(simulation=False):
    global api
    global person_id
    global passwd
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
    argsDefault={'BiasUpperLimit':2,\
                 'UpperLimitPosition':0.3,\
                 'BiasLowerLimit':0.5,\
                 'LowerLimitPosition':0.7,\
                 'BiasPeriod':20}
    #only int or float is supported right now
    def __init_(self):
        pass
    def createsignal(self,kbars_daily,parameters):
        dayhigh=kbars_daily['High']        
        daylow =kbars_daily['Low'] 
        dayclose=kbars_daily['Close']
        
        BiasUpperLimit=parameters['BiasUpperLimit']
        UpperLimitPosition=parameters['UpperLimitPosition']
        BiasLowerLimit=parameters['BiasLowerLimit']
        LowerLimitPosition=parameters['LowerLimitPosition']
        BiasPeriod=parameters['BiasPeriod']
        Bias=dayclose/dayclose.rolling(window=BiasPeriod).mean()
        Bias=Bias.fillna(method='bfill')
        
        positiondiff=UpperLimitPosition-LowerLimitPosition
        biasdiff=BiasUpperLimit-BiasLowerLimit
        position=LowerLimitPosition+(Bias-BiasLowerLimit)*positiondiff/biasdiff
        position[Bias<=BiasLowerLimit]=LowerLimitPosition
        position[Bias>=BiasUpperLimit]=UpperLimitPosition
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
        BiasUpperLimit=previouslist[0]
        UpperLimitPosition=previouslist[1]
        BiasLowerLimit=previouslist[2]
        LowerLimitPosition=previouslist[3]
        BiasPeriod=previouslist[4]
        if BiasLowerLimit>=BiasUpperLimit:
            return
        if LowerLimitPosition<=UpperLimitPosition:
            return
        parameters={'BiasUpperLimit':BiasUpperLimit,\
                    'UpperLimitPosition':UpperLimitPosition,\
                    'BiasLowerLimit':BiasLowerLimit,\
                    'LowerLimitPosition':LowerLimitPosition,\
                    'BiasPeriod':BiasPeriod,\
                    }
        buy=self.createsignal(kbars_daily,parameters)
        if(buy.min()<0):
            print('fail')
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

import datetime
class GridBot:
    upperid='006208'
    lowperid='00646'
    upperprice=0
    uppershare=0
    lowerprice=0
    lowershare=0
    uppershareTarget=0
    lowershareTarget=0
    MA=0
    money=0

    parameters={'BiasUpperLimit':1.1,\
                 'UpperLimitPosition':0.1,\
                 'BiasLowerLimit':0.9,\
                 'LowerLimitPosition':0.9,\
                 'BiasPeriod':50}
    
    year=0
    month=0
    day=0
    def __init__(self,uppershare=0,lowershare=0,money=10000):
        self.money=money
        self.uppershare=uppershare
        self.lowershare=lowershare
        
        
    def updateOrder(self):
        #1.update price
        #2.update Grid position
        #3.check order exist
        #3.1 if order exist, update order(跟內外盤的限價單)
        #test with buy: bid*0.9
        #tesst with sell: ask*1.1
        #3.2 if order not exist, create order(跟內外盤的限價單)
        #test with buy: bid*0.9
        #tesst with sell: ask*1.1
        pass
    
    def calculateSharetarget(self,upperprice,lowerprice):
        MA=self.MA
        uppershare=self.uppershare
        lowershare=self.lowershare
        money=self.money
        
        capitalInBot=money+uppershare*upperprice+lowershare*lowerprice
        #print("capitalInBot:",capitalInBot)
        #print("lowershare:",lowershare)
       # print("uppershare:",uppershare)
       # print("lowerprice:",lowerprice)
       # print("upperprice:",upperprice)
        #計算目標部位百分比
        Bias=(upperprice/lowerprice)/MA
        BiasUpperLimit=self.parameters['BiasUpperLimit']
        UpperLimitPosition=self.parameters['UpperLimitPosition']
        BiasLowerLimit=self.parameters['BiasLowerLimit']
        LowerLimitPosition=self.parameters['LowerLimitPosition']
        BiasPeriod=self.parameters['BiasPeriod']
        
        shareTarget=(Bias-BiasLowerLimit)/(BiasUpperLimit-BiasLowerLimit)
        shareTarget=shareTarget*(UpperLimitPosition-LowerLimitPosition)
        shareTarget=max(shareTarget,UpperLimitPosition)
        shareTarget=min(shareTarget,LowerLimitPosition)
        #print("shareTarget:",shareTarget)
        #計算目標部位(股數)
        self.uppershareTarget=int(shareTarget*capitalInBot/upperprice)
        self.lowershareTarget=int((1.0-shareTarget)*capitalInBot/lowerprice)
        self.upperprice=upperprice
        self.lowerprice=lowerprice
        
    
    def UpdateMA(self):
        now = datetime.datetime.now()
        if(now.year!=self.year and now.month!= self.month and  now.day!=self.day):
            print('reading upper')
            upper = yf.Ticker(self.upperid+".tw")
            upper_hist = upper.history(period="3mo")
            period=self.parameters['BiasPeriod']
       
            upper_close=upper_hist['Close']
            upperMA=upper_close[-(period+1):-1].sum()/period
            if(self.lowperid!='Cash'):
                print('reading lower')
                lower = yf.Ticker(self.lowperid+".tw")
                lower_hist = lower.history(period="3mo")
                lower_close=lower_hist['Close']
                close=(upper_close/lower_close).dropna()
                self.MA=close[-(period+1):-1].sum()/period
            else:
                close=upper_close.dropna()
                self.MA=close[-(period+1):-1].sum()/period
            self.year=now.year 
            self.month=now.month 
            self.day=now.day
    
            

shioajiLogin(simulation=False)
contract_006208 = api.Contracts.Stocks["006208"]
contract_00646 = api.Contracts.Stocks["00646"]
portfolio=api.list_positions(unit=shioaji.constant.Unit.Share)
CA='c:\ekey\\551\\'+person_id+'\\S\\Sinopac.pfx'
CA_passwd=input("Please input CA PASSWORD:\n")
result = api.activate_ca(\
    ca_path=CA,\
    ca_passwd=CA_passwd,\
    person_id=person_id,\
)
CA_passwd=0
person_id=0
passwd=0
api.update_status()
#stockpositions=api.list_positions(api.stock_account)
#df_positions = pd.DataFrame(stockpositions)
#api.list_positions(api.future_account)

bot1=GridBot(uppershare=0,lowershare=0,money=10000)
import threading, time
from threading import Thread, Lock

mutexDict ={'006208':Lock(),'00646':Lock()}
mutexBidAskDict ={'006208':Lock(),'00646':Lock()}
subscribeStockList=['006208','00646']
snapshots={}
snapshots['006208'] = api.snapshots([api.Contracts.Stocks['006208']])
snapshots['00646'] = api.snapshots([api.Contracts.Stocks['00646']])

#抓取創建BOT當下的價格當作預設值
stockPrice={'006208':snapshots['006208'][0]['close'],\
            '00646' :snapshots['00646'][0]['close']}
stockBid={'006208':snapshots['006208'][0]['close'],\
            '00646' :snapshots['00646'][0]['close']}
stockAsk={'006208':snapshots['006208'][0]['close'],\
            '00646' :snapshots['00646'][0]['close']}

def jobs_per1min():
    while(1):
        bot1.UpdateMA()
        print('UpdateMA Done')
        #get price 
        mutexDict['006208'].acquire()
        mutexDict['00646'].acquire()
        mutexBidAskDict['006208'].acquire()
        mutexBidAskDict['00646'].acquire()
        if(stockPrice['006208']>stockAsk['006208'] or stockPrice['006208']<stockBid['006208']):
            stockPrice['006208']=(stockAsk['006208']+stockBid['006208'])/2
        if(stockPrice['00646']>stockAsk['00646'] or stockPrice['00646']<stockBid['00646']):
            stockPrice['00646']=(stockAsk['00646']+stockBid['00646'])/2
        mutexDict['00646'].release()
        mutexDict['006208'].release()
        mutexBidAskDict['00646'].release()
        mutexBidAskDict['006208'].release()
        
        #update share target
        bot1.calculateSharetarget(upperprice=stockPrice['006208']\
                                  ,lowerprice=stockPrice['00646'])
        #update orders
            
        current_time = time.time()
        time_to_sleep = 60 - (current_time % 60)
        time.sleep(time_to_sleep)

thread = threading.Thread(target=jobs_per1min)
thread.start()


tick_006208=api.quote.subscribe(\
    contract_006208,\
    quote_type = shioaji.constant.QuoteType.Tick,\
    version = shioaji.constant.QuoteVersion.v1,\
    intraday_odd = True
)
bidask006208=api.quote.subscribe(\
    contract_006208,\
    quote_type = shioaji.constant.QuoteType.BidAsk,\
    version = shioaji.constant.QuoteVersion.v1,\
    intraday_odd=True
)

tick_00646=api.quote.subscribe(\
    contract_00646,\
    quote_type = shioaji.constant.QuoteType.Tick,\
    version = shioaji.constant.QuoteVersion.v1,\
    intraday_odd = True
)
bidask00646=api.quote.subscribe(\
    contract_00646,\
    quote_type = shioaji.constant.QuoteType.BidAsk,\
    version = shioaji.constant.QuoteVersion.v1,\
    intraday_odd=True
)    

from shioaji import BidAskSTKv1, Exchange,TickSTKv1
@api.on_tick_stk_v1()
def STKtick_callback(exchange: Exchange, tick:TickSTKv1):
    code=tick['code']
    mutexDict[code].acquire()
    stockPrice[code]=float(tick['close'])
    mutexDict[code].release()
    #print(f"Exchange: {exchange}, Tick: {tick}")    
api.quote.set_on_tick_stk_v1_callback(STKtick_callback)

@api.on_bidask_stk_v1()
def STK_BidAsk_callback(exchange: Exchange, bidask:BidAskSTKv1):
    code=bidask['code']
    mutexBidAskDict[code].acquire()
    stockBid[code]=float(bidask['bid_price'][0])
    stockAsk[code]=float(bidask['ask_price'][0])
    mutexBidAskDict[code].acquire()
    #print(f"Exchange: {exchange}, BidAsk: {bidask}")
api.quote.set_on_bidask_stk_v1_callback(STK_BidAsk_callback)

@api.quote.on_event
def event_callback(resp_code: int, event_code: int, info: str, event: str):
    print(f'Event code: {event_code} | Event: {event}')
api.quote.set_event_callback(event_callback)

'''
api.quote.unsubscribe(    contract_006208,\
    quote_type = shioaji.constant.QuoteType.Tick,\
    version = shioaji.constant.QuoteVersion.v1,\
    intraday_odd = True)
api.quote.unsubscribe(    contract_006208,\
    quote_type = shioaji.constant.QuoteType.BidAsk,\
    version = shioaji.constant.QuoteVersion.v1,\
    intraday_odd=True)
api.quote.unsubscribe(    contract_00646,\
    quote_type = shioaji.constant.QuoteType.Tick,\
    version = shioaji.constant.QuoteVersion.v1,\
    intraday_odd = True)
api.quote.unsubscribe(    contract_00646,\
    quote_type = shioaji.constant.QuoteType.BidAsk,\
    version = shioaji.constant.QuoteVersion.v1,\
    intraday_odd=True)
'''