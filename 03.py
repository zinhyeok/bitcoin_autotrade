from os import access, remove
from re import L
import time
from numpy import NaN, absolute
import pyupbit
import datetime
import pandas as pd
from pyupbit.quotation_api import get_tickers
import requests
import pytz


def get_sort50(tickers):
    df = pd.DataFrame()
    for ticker in tickers:
        try:
            temp = pyupbit.get_ohlcv(ticker, interval="day", count=1)
            temp["ticker"] = ticker
            df = pd.concat([df, temp])
        except:
            pass
    # 결측치 데이터 삭제
    df.dropna(inplace=True)
    df_sort_top50 = df.sort_values(by='volume', ascending=False).groupby(
        'ticker', sort=False).head(30)
    sort_coin50 = df_sort_top50['ticker'].values.tolist()
    return sort_coin50


tickers = pyupbit.get_tickers(fiat="KRW")
sort_coin50 = get_sort50(tickers)
print(sort_coin50)
