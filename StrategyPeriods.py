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
PeriodRanges['720m']=np.arange(2,21,2)
PeriodRanges['360m']=np.arange(2,21,2)
PeriodRanges['180m']=np.arange(2,21,2)
PeriodRanges['120m']=np.arange(2,21,2)
PeriodRanges['60m']=np.arange(2,21,2)
PeriodRanges['12h']=PeriodRanges['720m']
PeriodRanges['6h']=PeriodRanges['360m']
PeriodRanges['3h']=PeriodRanges['180m']
PeriodRanges['2h']=PeriodRanges['120m']
PeriodRanges['1h']=PeriodRanges['60m']