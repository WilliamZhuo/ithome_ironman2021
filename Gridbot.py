from shioaji.data import Kbars
import pandas as pd
import shioaji
import shioaji.order as stOrder
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np
import ShiojiLogin
from  ShiojiLogin import shioajiLogin
import os
import logging
import pickle
DEBUG_MODE=True
DEBUG_SELLALOT=True
ENABLE_PREMARKET=True
REBOOT_HOUR=16
END_WEEKDAY=4 # Friday
#https://stackoverflow.com/questions/9847213/how-do-i-get-the-day-of-week-given-a-date
ans=''
api=ShiojiLogin.api
g_settlement=0

def GridbotBody():
    global g_settlement
    g_settlement=0
    global ans
    logging.basicConfig(filename='gridbotlog.log', level=logging.DEBUG)
    trigger=2000
    import datetime
    g_upperid='0052'
    g_lowerid='00662'
    
    initmoney=0
    
    class GridBot:
        upperid=g_upperid
        lowerid=g_lowerid
        upperprice=0
        uppershare=0
        lowerprice=0
        lowershare=0
        uppershareTarget=0
        lowershareTarget=0
        MA=0
        money=0
    
        parameters={'BiasUpperLimit':2.2,\
                 'UpperLimitPosition':0.1,\
                 'BiasLowerLimit':0.9,\
                 'LowerLimitPosition':0.9,\
                 'BiasPeriod':55}
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
                thisstatus=thistrade.status.status
                isCancelled=( thisstatus == stOrder.Status.Cancelled)
                isFailed=( thisstatus == stOrder.Status.Failed)
                isFilled=( thisstatus ==  stOrder.Status.Filled)
                isInactive=( thisstatus ==  stOrder.Status.Inactive)
                isPartFilled=( thisstatus ==  stOrder.Status.PartFilled)
                isPendingSubmit=( thisstatus ==  stOrder.Status.PendingSubmit)
                isPreSubmitted=( thisstatus ==  stOrder.Status.PreSubmitted)            
                isSubmitted=( thisstatus ==  stOrder.Status.Submitted)
                
                cond1=not(\
                          isCancelled\
                          or  isFailed\
                          or  isFilled\
                          ) 
                cond2=thistrade.contract.code==self.upperid
                cond3=thistrade.contract.code==self.lowerid
                cond4=self.lowerid!='Cash'
                if(cond1 and cond2):
                    tradeUpper.append(thistrade)
                if(cond1 and cond3 and cond4):
                    tradeLower.append(thistrade)
            
            for i in range(0,len(tradeUpper),1):
                api.update_status()
                api.cancel_order(trade=tradeUpper[i])
            if(self.lowerid!='Cash'):
                for i in range(0,len(tradeLower),1):
                    api.update_status()
                    api.cancel_order(trade=tradeLower[i])
                    
        def getPositions(self):
            api.update_status()
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
            quantityUpper=min(quantityUpper,999)
            quantityUpper=max(quantityUpper,-999)
            quantityLower=min(quantityLower,999)
            quantityLower=max(quantityLower,-999)
            logging.debug('uppershare:'+str(self.uppershare))
            logging.debug('lowershare:'+str(self.lowershare))
            logging.debug('uppershareTarget:'+str(self.uppershareTarget))
            logging.debug('lowershareTarget:'+str(self.lowershareTarget))
            logging.debug('quantityUpper:'+str(quantityUpper))
            logging.debug('quantityLower:'+str(quantityLower))
            
            val=self.uppershareTarget*self.upperprice+self.lowerprice*self.lowershareTarget
            
            code=self.upperid
            money=self.money
            logging.debug('money1:'+str(money))
            if(quantityUpper>0):
                cost=stockBid[code]*quantityUpper
                if(money<cost):
                    quantityUpper=max(int(money/stockBid[code]),0)
            quantityUpperValid=abs(quantityUpper)>0
            if(quantityUpperValid):
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
                    logging.debug(code+' buy:')
                    logging.debug('quantity:'+str(quantityUpper))
                    logging.debug('price:'+str(stockBid[code]))
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
                    logging.debug(code+' sell:')
                    logging.debug('quantity:'+str(abs(quantityUpper)))
                    logging.debug('price:'+str(stockAsk[code]))
                    
                if(abs(quantityUpper)*stockPrice[code]>=trigger):    
                    contract = api.Contracts.Stocks[code]
                    cost=stockBid[code]*quantityUpper
                    if(quantityUpper>0):
                        if(money>cost):
                            money=money-cost #local money int
                            trade = api.place_order(contract, order)
                    else:
                        trade = api.place_order(contract, order)
            logging.debug('money2:'+str(money))
            code=self.lowerid
            if(quantityLower>0):
                cost=stockBid[code]*quantityLower
                if(money<cost):
                    quantityLower=max(int(money/stockBid[code]),0)
            quantityLowerValid=abs(quantityLower)>0
            if(self.lowerid!='Cash' and quantityLowerValid):
                if(quantityLower>0):
                    logging.debug(code+' buy:')
                    logging.debug('quantity:'+str(quantityLower))
                    logging.debug('price:'+str(stockBid[code]))
                    order = api.Order(
                        price=stockBid[code],
                        quantity=quantityLower,
                        action=shioaji.constant.Action.Buy,
                        price_type=shioaji.constant.StockPriceType.LMT,
                        order_type=shioaji.constant.TFTOrderType.ROD,     
                        order_lot=shioaji.constant.TFTStockOrderLot.IntradayOdd, 
                        account=api.stock_account,
                    )
                else:
                    logging.debug(code+' sell:')
                    logging.debug('quantity:'+str(abs(quantityLower)))
                    logging.debug('price:'+str(stockAsk[code]))
                    order = api.Order(
                        price=stockAsk[code],
                        quantity=-quantityLower,
                        action=shioaji.constant.Action.Sell,
                        price_type=shioaji.constant.StockPriceType.LMT,
                        order_type=shioaji.constant.TFTOrderType.ROD,     
                        order_lot=shioaji.constant.TFTStockOrderLot.IntradayOdd, 
                        account=api.stock_account,
                    )
                if(abs(quantityLower)*stockPrice[code]>=trigger):    
                    contract = api.Contracts.Stocks[code]
                    cost=stockBid[code]*quantityLower
                    if(quantityLower>0):
                        if(money>cost):
                            money=money-cost
                            trade = api.place_order(contract, order)
                    else:
                        trade = api.place_order(contract, order)
                        
        def updateOrder(self):
    
            try:
                #1.delete orders
                logging.debug('cancelOrders')
                self.cancelOrders()
                #2.update positions
                logging.debug('getPositions')
                self.getPositions()
                #3.update share target
                logging.debug('calculateSharetarget')
                self.calculateSharetarget(upperprice=stockPrice[g_upperid]\
                                          ,lowerprice=stockPrice[g_lowerid])
                #4.create orders
                logging.debug('sendOrders')
                self.sendOrders()
            except Exception as e: # work on python 3.x
                logging.error('updateOrder Error Message: '+ str(e))
        
        def calculateSharetarget(self,upperprice,lowerprice):
            global accountCash
            now = datetime.datetime.now()
            hour=now.hour
            
            if(hour>=1 and hour<=7):
                self.money=initmoney+g_settlement
            else:
                self.money=initmoney+g_settlement
                
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
            uppershareTarget=int(shareTarget*capitalInBot/upperprice)
            lowershareTarget=int((1.0-shareTarget)*capitalInBot/lowerprice)
            upperprice=upperprice
            lowerprice=lowerprice
            val=uppershareTarget*upperprice+lowerprice*lowershareTarget
    
            self.uppershareTarget=uppershareTarget
            self.lowershareTarget=lowershareTarget
            self.upperprice=upperprice
            self.lowerprice=lowerprice
        
        def UpdateMA(self):
            now = datetime.datetime.now()
            if(now.year!=self.year or now.month!= self.month or  now.day!=self.day):
                logging.debug('reading upper')
                upper = yf.Ticker(self.upperid+".tw")
                upper_hist = upper.history(period="3mo")
                period=self.parameters['BiasPeriod']
           
                upper_close=upper_hist['Close']
                upperMA=upper_close[-(period+1):-1].sum()/period
                if(self.lowerid!='Cash'):
                    logging.debug('reading lower')
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
        global accountCash
        
        #?????????
        settlement = api.list_settlements(api.stock_account) 
        logging.debug(settlement)
        df_settlement = pd.DataFrame(settlement)     
        cash_setttlement=float(df_settlement['t1_money'])+float(df_settlement['t2_money'])
        #bank cash
        acc_balance = api.account_balance()   
        df_acc = pd.DataFrame(acc_balance)    
        logging.debug(acc_balance) 
        acc_f=float(df_acc['acc_balance'])
        if(acc_f>0):
            return  acc_f+cash_setttlement
        else:
            return  accountCash
            
    def pickle_dump(filename,obj):
        with open(filename, 'wb') as handle:
            pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)
            
    def pickle_read(filename):
        with open(filename, 'rb') as handle:
            return pickle.load(handle)
        
    snaprice={}
    snaprice[g_upperid] = api.snapshots([api.Contracts.Stocks[g_upperid]])
    snaprice[g_lowerid] = api.snapshots([api.Contracts.Stocks[g_lowerid]])
    stockPrice={g_upperid:snaprice[g_upperid][0]['close'],\
                g_lowerid:snaprice[g_lowerid][0]['close']}
    stockBid={g_upperid:snaprice[g_upperid][0]['close'],\
              g_lowerid:snaprice[g_lowerid][0]['close']}
    stockAsk={g_upperid:snaprice[g_upperid][0]['close'],\
              g_lowerid:snaprice[g_lowerid][0]['close']}
        
    accountCash=getCash()
    bot1=GridBot(uppershare=0,lowershare=0,money=0)
    bot1.getPositions()
    
    try:
        initmoney=pickle_read('money.p')
    except:
        initmoney=0
    totalcapital=initmoney+stockPrice[g_upperid]*bot1.uppershare+stockPrice[g_lowerid]*bot1.lowershare
    trigger=max(2000,totalcapital*0.005)
    print("totalcapital is "+str(totalcapital))
    if(ans==''):
        ans=input("perform withdraw or deposit(y/n):\n")
        if(ans=='y'):
            amount=input("withdraw or deposit amount(>0:deposit,<0:withdraw):\n")
            initmoney=initmoney+int(amount)
    bot1.money=initmoney
    import threading, time
    from threading import Thread, Lock
    
    mutexDict ={g_upperid:Lock(),g_lowerid:Lock()}
    mutexBidAskDict ={g_upperid:Lock(),g_lowerid:Lock()}
    subscribeStockList=[g_upperid,g_lowerid]
    
    #????????????BOT??????????????????????????????
    msglist=[]
    statlist=[]
    
    mutexmsg =Lock()
    mutexstat =Lock()
    mutexgSettle =Lock()
    g_settlement=0
    def place_cb(stat, msg):
        logging.debug('my_place_callback')
        logging.debug(str(stat))
        logging.debug(str(msg))
        if(len(msg)==13):
            global g_settlement
            action=msg['action']
            code=msg['code']
            price=msg['price']
            quantity=msg['quantity']
            mutexgSettle.acquire()
            if(action=='Buy'):
                g_settlement-=price*quantity
            elif(action=='Sell'):
                g_settlement+=price*quantity
            else:
                pass
            mutexgSettle.release()
        mutexmsg.acquire()
        try:
            msglist.append(msg)
        except Exception as e: # work on python 3.x
            logging.error('place_cb  Error Message A: '+ str(e))
        mutexmsg.release()    
        mutexstat.acquire()
        try:
            statlist.append(stat)
        except Exception as e: # work on python 3.x
            logging.error('place_cb  Error Message B: '+ str(e))
        mutexstat.release()
    
    api.set_order_callback(place_cb)
    
        
    def jobs_per1min():
        while(1):
            current_time = time.time()
            cooldown=60
            time_to_sleep = cooldown - (current_time % cooldown)
            time.sleep(time_to_sleep)
            
            #only trigger once per day
            bot1.UpdateMA()
            logging.debug('UpdateMA Done')
            logging.debug('g_settlement:'+str(g_settlement))
            
            now = datetime.datetime.now()
            hour=now.hour
            minute=now.minute
            second=now.second
            if(minute%3==0 and second>=30):
                continue
            if(minute%3==1 and second<=30):
                continue
            if(hour==13 and minute>20):
                try:
                    bot1.cancelOrders()
                except Exception as e:
                    logging.error('jobs_per1min  Error Message A: '+ str(e))
                continue
            if(hour>=14 and hour<=15):
                pickle_dump( "money.p",bot1.money)
                break
            if(not ENABLE_PREMARKET):
     
                if(hour<9 or (hour>13)):
                    continue
                
            #get price 
            mutexDict[g_upperid].acquire()
            mutexDict[g_lowerid].acquire()
            mutexBidAskDict[g_upperid].acquire()
            mutexBidAskDict[g_lowerid].acquire()
            if(stockPrice[g_upperid]>stockAsk[g_upperid] or stockPrice[g_upperid]<stockBid[g_upperid]):
                stockPrice[g_upperid]=(stockAsk[g_upperid]+stockBid[g_upperid])/2
            if(stockPrice[g_lowerid]>stockAsk[g_lowerid] or stockPrice[g_lowerid]<stockBid[g_lowerid]):
                stockPrice[g_lowerid]=(stockAsk[g_lowerid]+stockBid[g_lowerid])/2
            mutexDict[g_lowerid].release()
            mutexDict[g_upperid].release()
            mutexBidAskDict[g_lowerid].release()
            mutexBidAskDict[g_upperid].release()   
            #update orders
            bot1.updateOrder()
    
    
    contract_006208 = api.Contracts.Stocks[g_upperid]
    contract_00646 = api.Contracts.Stocks[g_lowerid]
    
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
        
        logging.debug('bid_price') 
        for i in bidask['bid_price']:
            logging.debug(str(i))     
        logging.debug('ask_price') 
        for i in bidask['ask_price']:
            logging.debug(str(i)) 
            
        bidlist=[float(i) for i in bidask['bid_price']]
        asklist=[float(i) for i in bidask['ask_price']]
    
        #stockBid[code]=max(bidlist)
        #stockAsk[code]=min(asklist)
        stockBid[code]=bidlist[0]
        stockAsk[code]=asklist[0]
        mutexBidAskDict[code].release()
        #print(f"Exchange: {exchange}, BidAsk: {bidask}")
    api.quote.set_on_bidask_stk_v1_callback(STK_BidAsk_callback)
    
    @api.quote.on_event
    def event_callback(resp_code: int, event_code: int, info: str, event: str):
        logging.debug(f'Event code: {event_code} | Event: {event}')
    api.quote.set_event_callback(event_callback)

    jobs_per1min()
    
GridbotBody()
import datetime
import time
while(1):         
    #check reboot once per minute
    current_time = time.time()
    cooldown=60
    time_to_sleep = cooldown - (current_time % cooldown)
    time.sleep(time_to_sleep)
    
    #check weekday and hour
    now = datetime.datetime.now()
    hour=now.hour
    weekday= now.weekday()
    print('hour:',hour)
    if(hour==REBOOT_HOUR):
        print('reboot bot')
        api.logout()
        api=ShiojiLogin.shioajiLogin(simulation=False)
        GridbotBody()
    if(END_WEEKDAY==weekday):
        break