from os import access
import time
from numpy import absolute
import pyupbit
import datetime
import pandas as pd

f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()  # \n 제거
secret = lines[1].strip()
f.close()

# Upbit class instance, object 만드느 과정
upbit = pyupbit.Upbit(access, secret)


# def get_target_noise(ticker, day):
# #20일 평균 noise를 기본으로 구성
# 노이즈 = 1-abs(시가-종가)/고가-저가 → 노이즈가 0.4 정도여야 함
# to-do 값중 none data 어떻게 처리?
tickers = pyupbit.get_tickers(fiat="KRW")
# tikcers 배열로 가져움  KRW-~ 형태
df = pd.DataFrame()
for ticker in tickers:
    try:
        temp = pyupbit.get_ohlcv(ticker, interval="day", count=20)
        temp["ticker"] = ticker
        df = pd.concat([df, temp])
        temp["noise"] = 1 - (
            absolute(df["open"] - df["close"]) / absolute(df["high"] - df["low"])
        )
        # temp["noise"] = 1 - (
        #     absolute(df["open"] - df["close"]) / absolute(df["high"] - df["low"])
        # )
        # df = pd.concat([df, temp])
    except:
        pass

        df = pd.concat([df, temp])

df.to_excel("coinohlcv_20day.xlsx")
# 1~20(1 - absdf.open - df.close) / (df.high - df.low))/20


# def get_target_price(ticker, k):
#     """변동성 돌파 전략으로 매수 목표가 조회"""
#     df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
#     target_price = df.iloc[0]["close"] + (df.iloc[0]["high"] - df.iloc[0]["low"]) * k
#     return target_price


# def get_start_time(ticker):
#     """시작 시간 조회"""
#     df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
#     start_time = df.index[0]
#     return start_time


# def get_balance(ticker):
#     """잔고 조회"""
#     balances = upbit.get_balances()
#     for b in balances:
#         if b["currency"] == ticker:
#             if b["balance"] is not None:
#                 return float(b["balance"])
#             else:
#                 return 0
#     return 0


# def get_current_price(ticker):
#     """현재가 조회"""
#     return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]


# # 로그인
# upbit = pyupbit.Upbit(access, secret)
# print("autotrade start")

# # 자동매매 시작
# while True:
#     try:
#         now = datetime.datetime.now()
#         start_time = get_start_time("KRW-BTC")
#         end_time = start_time + datetime.timedelta(days=1)

#         if start_time < now < end_time - datetime.timedelta(seconds=10):
#             target_price = get_target_price("KRW-BTC", 0.5)
#             current_price = get_current_price("KRW-BTC")
#             if target_price < current_price:
#                 krw = get_balance("KRW")
#                 if krw > 5000:
#                     upbit.buy_market_order("KRW-BTC", krw * 0.9995)
#         else:
#             btc = get_balance("BTC")
#             if btc > 0.00008:
#                 upbit.sell_market_order("KRW-BTC", btc * 0.9995)
#         time.sleep(1)
#     except Exception as e:
#         print(e)
#         time.sleep(1)
