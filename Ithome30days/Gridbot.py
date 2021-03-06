from shioaji.data import Kbars
import pandas as pd
import shioaji
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np
import ShiojiLogin
api=ShiojiLogin.api

import datetime
class GridBot:
    upperid='006208'
    lowerid='00646'
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
        self.contractUpper = api.Contracts.Stocks[self.upperid]
        self.contractLower = api.Contracts.Stocks[self.lowerid]
        
    def cancelOrders(self):
        api.update_status()
        tradelist=api.list_trades()
        tradeUpper=[]
        tradeLower=[]
        for i in range(0,len(tradelist),1):
            thistrade=tradelist[i]
            cond1=str(thistrade.status.status)=='Status.Submitted'\
                or str(thistrade.status.status)=='Status.PartFilled'
            cond2=thistrade.contract.code==self.upperid
            cond3=thistrade.contract.code==self.lowerid
            cond4=self.lowerid!='Cash'
            if(cond1 and cond2):
                tradeUpper.append(thistrade)
            if(cond1 and cond3 and cond4):
                tradeLower.append(thistrade)
        
        for i in range(0,len(tradeUpper),1):
            api.cancel_order(trade=tradeUpper[i])
        if(self.lowerid!='Cash'):
            for i in range(0,len(tradeLower),1):
                api.cancel_order(trade=tradeLower[i])
                
    def getPositions(self):
        portfolio=api.list_positions(unit=shioaji.constant.Unit.Share)
        df_positions = pd.DataFrame(portfolio)
        quantity=df_positions.loc[df_positions['code'] == self.upperid]['quantity']
        if(quantity.size==0):
            self.uppershare=0
        else:
            self.uppershare=int(quantity)
        if(self.lowerid!='Cash'):
            quantity=df_positions.loc[df_positions['code'] == self.lowerid]['quantity']
            if(quantity.size==0):
                self.lowershare=0
            else:
                self.lowershare=int(quantity)
                
    def sendOrders(self):
        quantityUpper=self.uppershareTarget-self.uppershare
        quantityLower=self.lowershareTarget-self.lowershare
        
        code=self.upperid
        money=self.money
        if(quantityUpper>0):
            order = api.Order(
                price=stockBid[code],
                quantity=quantityUpper,
                action=shioaji.constant.Action.Buy,
                price_type=shioaji.constant.StockPriceType.LMT,
                order_type=shioaji.constant.TFTOrderType.ROD,     
                order_lot=shioaji.constant.TFTStockOrderLot.IntradayOdd, 
                account=api.stock_account,
            )
            print(code,' buy:')
            print('quantity:',quantityUpper)
            print('price:',stockBid[code])
        else:
            order = api.Order(
                price=stockAsk[code],
                quantity=abs(quantityUpper),
                action=shioaji.constant.Action.Sell,
                price_type=shioaji.constant.StockPriceType.LMT,
                order_type=shioaji.constant.TFTOrderType.ROD,     
                order_lot=shioaji.constant.TFTStockOrderLot.IntradayOdd, 
                account=api.stock_account,
            )
            print(code,' sell:')
            print('quantity:',abs(quantityUpper))
            print('price:',stockAsk[code])
            
        if(abs(quantityUpper)*stockPrice[code]>=2000):    
            contract = api.Contracts.Stocks[code]
            cost=stockBid[code]*quantityUpper
            if(quantityUpper>0):
                if(money>cost):
                    money=money-cost
                    trade = api.place_order(contract, order)
            else:
                trade = api.place_order(contract, order)
                
        if(self.lowerid!='Cash'):
            code=self.lowerid
            if(quantityLower>0):
                order = api.Order(
                    price=stockBid[code],
                    quantity=quantityLower,
                    action=shioaji.constant.Action.Buy,
                    price_type=shioaji.constant.StockPriceType.LMT,
                    order_type=shioaji.constant.TFTOrderType.ROD,     
                    order_lot=shioaji.constant.TFTStockOrderLot.IntradayOdd, 
                    account=api.stock_account,
                )
                print(code,' buy:')
                print('quantity:',quantityLower)
                print('price:',stockBid[code])
            else:
                order = api.Order(
                    price=stockAsk[code],
                    quantity=-quantityLower,
                    action=shioaji.constant.Action.Sell,
                    price_type=shioaji.constant.StockPriceType.LMT,
                    order_type=shioaji.constant.TFTOrderType.ROD,     
                    order_lot=shioaji.constant.TFTStockOrderLot.IntradayOdd, 
                    account=api.stock_account,
                )
                print(code,' sell:')
                print('quantity:',abs(quantityLower))
                print('price:',stockAsk[code])
            if(abs(quantityLower)*stockPrice[code]>=2000):    
                contract = api.Contracts.Stocks[code]
                cost=stockBid[code]*quantityLower
                if(quantityLower>0):
                    if(money>cost):
                        money=money-cost
                        trade = api.place_order(contract, order)
                else:
                    trade = api.place_order(contract, order)
                    
    def updateOrder(self):
        now = datetime.datetime.now()
        minute=now.minute
        second=now.second
        if(minute%3==0 and second>=30):
            return
        if(minute%3==1 and second<=30):
            return
        
        #1.delete orders
        self.cancelOrders()
        #2.update positions
        self.getPositions()
        #3.create orders
        self.sendOrders()
        
    
    def calculateSharetarget(self,upperprice,lowerprice):
        global accountCash
        currentcash=getCash()
        self.money+=currentcash-accountCash
        accountCash=currentcash
        
        MA=self.MA
        uppershare=self.uppershare
        lowershare=self.lowershare
        money=self.money
        
        capitalInBot=money+uppershare*upperprice+lowershare*lowerprice
        #???????????????????????????
       # print('MA:',MA)
       # print('upperprice:',upperprice)
       # print('lowerprice:',lowerprice)
        Bias=(upperprice/lowerprice)/MA
       # print('Bias:',Bias)
        
        BiasUpperLimit=self.parameters['BiasUpperLimit']
        UpperLimitPosition=self.parameters['UpperLimitPosition']
        BiasLowerLimit=self.parameters['BiasLowerLimit']
        LowerLimitPosition=self.parameters['LowerLimitPosition']
        BiasPeriod=self.parameters['BiasPeriod']
        
        shareTarget=(Bias-BiasLowerLimit)/(BiasUpperLimit-BiasLowerLimit)
        shareTarget=shareTarget*(UpperLimitPosition-LowerLimitPosition)+LowerLimitPosition
        shareTarget=max(shareTarget,UpperLimitPosition)
        shareTarget=min(shareTarget,LowerLimitPosition)
       # print('shareTarget:',shareTarget)
        #print("shareTarget:",shareTarget)
        #??????????????????(??????)
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
            if(self.lowerid!='Cash'):
                print('reading lower')
                lower = yf.Ticker(self.lowerid+".tw")
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
    
            
def getCash():
    #?????????
    settlement = api.list_settlements(api.stock_account)   
    df_settlement = pd.DataFrame(settlement)     
    cash_setttlement=float(df_settlement['t1_money'])+float(df_settlement['t2_money'])
    #bank cash
    acc_balance = api.account_balance()   
    df_acc = pd.DataFrame(acc_balance)     
         
    return  float(df_acc['acc_balance'])+cash_setttlement


accountCash=getCash()
bot1=GridBot(uppershare=0,lowershare=0,money=10000)
import threading, time
from threading import Thread, Lock

mutexDict ={'006208':Lock(),'00646':Lock()}
mutexBidAskDict ={'006208':Lock(),'00646':Lock()}
subscribeStockList=['006208','00646']
snapshots={}
snapshots['006208'] = api.snapshots([api.Contracts.Stocks['006208']])
snapshots['00646'] = api.snapshots([api.Contracts.Stocks['00646']])

#????????????BOT??????????????????????????????
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
            
        current_time = time.time()
        #update orders
        bot1.updateOrder()
        
        cooldown=60
        time_to_sleep = cooldown - (current_time % cooldown)
        time.sleep(time_to_sleep)

thread = threading.Thread(target=jobs_per1min)
thread.start()

contract_006208 = api.Contracts.Stocks["006208"]
contract_00646 = api.Contracts.Stocks["00646"]

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
    mutexBidAskDict[code].release()
    #print(f"Exchange: {exchange}, BidAsk: {bidask}")
api.quote.set_on_bidask_stk_v1_callback(STK_BidAsk_callback)

@api.quote.on_event
def event_callback(resp_code: int, event_code: int, info: str, event: str):
    print(f'Event code: {event_code} | Event: {event}')
api.quote.set_event_callback(event_callback)

