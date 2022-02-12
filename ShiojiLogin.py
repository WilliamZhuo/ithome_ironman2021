from shioaji.data import Kbars
import pandas as pd
import shioaji
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np
api=0
person_id=''#你的身分證字號
passwd=''#你的永豐證券登入密碼
CA_passwd=''
def shioajiLogin(simulation=False):
    global api
    global person_id
    global passwd
    global CA_passwd
    api = shioaji.Shioaji(simulation=simulation)

    if(person_id==''):
        person_id=input("Please input ID:\n")
    if(passwd==''):
        passwd=input("Please input PASSWORD:\n")
    if(CA_passwd==''):
        CA_passwd=input("Please input CA PASSWORD:\n")
    api.login(
        person_id=person_id, 
        passwd=passwd, 
        contracts_timeout=10000,
        contracts_cb=lambda security_type: print(f"{repr(security_type)} fetch done.")
    )
        
    
    CA='c:\ekey\\551\\'+person_id+'\\S\\Sinopac.pfx'
    result = api.activate_ca(\
        ca_path=CA,\
        ca_passwd=CA_passwd,\
        person_id=person_id,\
    )
    return api

shioajiLogin(simulation=False)