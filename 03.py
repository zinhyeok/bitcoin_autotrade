from os import access
import time
from numpy import absolute
import pyupbit
import datetime
import pandas as pd
import requests


def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]["close"] + (df.iloc[0]["high"] - df.iloc[0]["low"]) * k
    dict_target = {ticker: target_price}
    return dict_target


tickers = {"KRW-BTC", "KRW-OMG"}
for ticker in tickers:
    a = get_target_price(ticker, 0.5)
print(a)
