from shioaji.data import Kbars
import pandas as pd
import shioaji
api = shioaji.Shioaji(simulation=True)
person_id='PAPIUSER01'#你的身分證字號
passwd='2222'#你的永豐證券登入密碼
if(person_id==''):
    person_id=input("Please input ID:\n")
if(passwd==''):
    person_id=input("Please input PASSWORD:\n")
api.login(
    person_id=person_id, 
    passwd=passwd, 
    contracts_cb=lambda security_type: print(f"{repr(security_type)} fetch done.")
)

kbars = api.kbars(api.Contracts.Stocks["0050"], start="2010-01-01", end="2021-09-02")
df = pd.DataFrame({**kbars})
df.ts = pd.to_datetime(df.ts)
print(df)
close=df['Close']
close.index=df.ts

close['2021-09-02']

import datetime
date_begin=close.index[0].date()
date_end=close.index[-1].date()
delta = datetime.timedelta(days=1)

def create_PairForSeries(date,close):
    val=close[str(date)][-1]
    return pd.Series({date:val})  
dayclose=create_PairForSeries(date_begin,close)
date_begin += delta
while date_begin <= date_end:
    try:
        append=create_PairForSeries(date_begin,close)
        dayclose=dayclose.append(append)
    except:
        pass
    date_begin += delta
print(dayclose)