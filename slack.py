from os import access
from re import L
import time
from numpy import NaN, absolute
import pyupbit
import datetime
import pandas as pd
from pyupbit.quotation_api import get_tickers
import requests


def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time


now = datetime.datetime.now()
a = get_start_time("KRW-BTC")
print(a)
print(now)
tickers = pyupbit.get_tickers(fiat="KRW")
print(tickers)
