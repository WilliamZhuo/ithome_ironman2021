# -*- coding: utf-8 -*-
"""
Created on Wed Oct 13 22:57:04 2021

@author: user
"""
import numpy as np
'''
def getGeometricSequence(initial=2,length = 112,ratio = 1.05):
    progression = list(accumulate([ratio]*length, mul))
    return  np.array(progression)*initial    
l=getGeometricSequence()
l=l.astype(int)
l=np.unique(l)
'''
PeriodRanges={}
PeriodRanges['1d']=np.arange(2,61,2)
PeriodRanges['720min']=np.arange(2,21,2)
PeriodRanges['360min']=np.arange(2,21,2)
PeriodRanges['180min']=np.arange(2,21,2)
PeriodRanges['120min']=np.arange(2,21,2)
PeriodRanges['60min']=np.arange(2,21,2)
PeriodRanges['12h']=PeriodRanges['720min']
PeriodRanges['6h']=PeriodRanges['360min']
PeriodRanges['3h']=PeriodRanges['180min']
PeriodRanges['2h']=PeriodRanges['120min']
PeriodRanges['1h']=PeriodRanges['60min']