# -*- coding: utf-8 -*-
"""
Created on Sat Oct  2 15:43:37 2021

@author: user
"""
import Bars
import Strategies as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

tw = yf.Ticker("00692.tw")
TW_hist = tw.history(period="4y")
us = yf.Ticker("00646.tw")
US_hist = us.history(period="4y")
#兩邊歷史資料長度不一樣,取交集
idx = np.intersect1d(TW_hist.index, US_hist.index)
TW_hist = TW_hist.loc[idx]
US_hist = US_hist.loc[idx]


TW_open=TW_hist['Open']
TW_close=TW_hist['Close']
TW_high=TW_hist['High']
TW_low=TW_hist['Low']

US_open=US_hist['Open']
US_close=US_hist['Close']
US_high=US_hist['High']
US_low=US_hist['Low']

kbars = pd.DataFrame(\
    {'ts':TW_close.index\
    ,'Close':TW_close/US_close\
    ,'Open':TW_open/US_open\
    ,'High':TW_high/US_low\
    ,'Low':TW_low/US_high}).dropna() 

strategylist=[]

### others ####
strategylist.append(\
            st.struct_strategy_opt('SAR',st.strategy_SAR()))
strategylist.append(\
            st.struct_strategy_opt('MA',st.strategy_MA()))
strategylist.append(\
            st.struct_strategy_opt('MACD',st.strategy_MACD()))
strategylist.append(\
            st.struct_strategy_opt('BBAND',st.strategy_BBAND()))
strategylist.append(\
            st.struct_strategy_opt('RSI',st.strategy_RSI()))
strategylist.append(\
            st.struct_strategy_opt('BOP',st.strategy_BOP()))

#strategylist.append(\
#            st.struct_strategy_opt('grid',st.strategy_Grid()))
ret=st.optimizeListOfStrategies(kbars,strategylist)


### 跨市報酬計算 ###
buyTW=ret[2]
buyUS=1.0-buyTW

retTW,retseriesTW=st.backtest_signal(TW_open,buyTW,spread=0.0000176)
retUS,retseriesUS=st.backtest_signal(US_open,buyUS,spread=0.0000176)
retseries=(retseriesTW-1.0)+(retseriesUS-1.0)+1.0
prefixProfit=st.prefixProd(retseries)
plt.plot(prefixProfit,color='green')
#plt.plot(buyTW,color='red')
print('strategyMDD:',st.calculatMDD(prefixProfit))
print('USMDD:',st.calculatMDD(US_close))
print('TWMDD:',st.calculatMDD(TW_close))
print('strategyProfit:',prefixProfit.tolist()[-1]/prefixProfit.tolist()[0])
print('USProfit:',US_close.tolist()[-1]/US_close.tolist()[0])
print('TWProfit:',TW_close.tolist()[-1]/TW_close.tolist()[0])

