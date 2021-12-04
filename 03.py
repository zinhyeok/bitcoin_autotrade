from os import access
from re import S
import pyupbit
import pprint
import time
import datetime

f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()  # \n 제거
secret = lines[1].strip()
f.close()

# Upbit class instance, object 만드느 과정
upbit = pyupbit.Upbit(access, secret)
# balances 여러개 자산정보 + api 호출에 관한 것, balance는 한개(ticker 정하기)
mybalances = upbit.get_balances()
xrp_price = pyupbit.get_current_price("KRW-XRP")
print(mybalances)
# resp = upbit.buy_limit_order("")

# pprint.pprint()
# pprint.pprint(mybalances[0])
