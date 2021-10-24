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

import numpy as np
from itertools import accumulate
from operator import mul

import StrategyPeriods

PeriodRanges=StrategyPeriods.PeriodRanges
#periodlist=['1d','12h','6h','3h','2h','1h']
periodlist=['2h','1h']

retdict={}

raw=pd.read_csv('TWF.FIMTX HOT-TOUCHANCE-TWF-Futures-Minute-Trade.csv')
raw['DATETIME']=pd.to_datetime(raw['Date']+' '+raw['Time'])
raw=raw.set_index('DATETIME')
for period in periodlist:
    l=PeriodRanges[period]
    
    kbars = pd.DataFrame(columns = ['Open','High','Low','Close','Volume'])
    kbars['Open'] = raw['Open'].resample(period).first() #區間第一筆資料為開盤(Open)
    kbars['High'] = raw['High'].resample(period).max() #區間最大值為最高(High)
    kbars['Low'] = raw['Low'].resample(period).min() #區間最小值為最低(Low)
    kbars['Close'] = raw['Close'].resample(period).last() #區間最後一個值為收盤(Close)
    kbars['Volume'] = raw['TotalVolume'].resample(period).sum() #區間所有成交量加總
    kbars=kbars.dropna()
    
    
    strategylist=[]
    
    ### others ####
    
    
    MA_range=[l,l]
    strategylist.append(\
                st.struct_strategy_opt('MA'
                                       ,st.strategy_MA()
                                       ,MA_range)
                )
    
    
    MACD_range=[l,l,l]
    strategylist.append(\
                st.struct_strategy_opt('MACD'
                                       ,st.strategy_MACD()
                                       ,MACD_range)
                )
    
    BBAND_range=[l,np.arange(1.0,3.0,0.5),np.arange(1.0,3.0,0.5)]
    strategylist.append(\
                st.struct_strategy_opt('BBAND'
                                       ,st.strategy_BBAND()
                                       ,BBAND_range))
    
    strategylist.append(\
                st.struct_strategy_opt('BBAND_FOLLOWTREND'
                                       ,st.strategy_BBAND(st.strategy_BBAND.MODE.MODE_FOLLOWTREND)
                                       ,BBAND_range)
                )
    SAR_range=st.strategy_SAR().rangeDefault
    strategylist.append(\
                st.struct_strategy_opt('SAR'
                                       ,st.strategy_SAR()
                                       ,SAR_range)
                )
    
    RSI_range=[l,np.arange(0,110,10),np.arange(0,110,10)]
    strategylist.append(\
                st.struct_strategy_opt('RSI'
                                       ,st.strategy_RSI()
                                       ,RSI_range)
                )
    
    strategylist.append(\
                st.struct_strategy_opt('BOP',st.strategy_BOP()))
    
    #strategylist.append(\
    #            st.struct_strategy_opt('grid',st.strategy_Grid()))
    ret=st.optimizeListOfStrategies(kbars,strategylist)
    retdict[period]=ret
'''
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

'''