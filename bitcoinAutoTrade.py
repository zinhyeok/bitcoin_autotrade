from os import access
import time
from numpy import absolute
import pyupbit
import datetime
import pandas as pd
import requests


f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()  # \n 제거
secret = lines[1].strip()
f.close()

# Upbit class instance, object 만드는 과정
upbit = pyupbit.Upbit(access, secret)

# slack에 메세지 봇 추가
def post_message(token, channel, text):
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + token},
        data={"channel": channel, "text": text},
    )
    print(response)


myToken = "xoxb-2799366043639-2816286941284-yDDBBjbHhbeGp0xIhnwW3I5c"


#####함수 모음

# 매수 목표가 조회
def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]["close"] + (df.iloc[0]["high"] - df.iloc[0]["low"]) * k
    return target_price


# 잔고조회
def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b["currency"] == ticker:
            if b["balance"] is not None:
                return float(b["balance"])
            else:
                return 0
    return 0


# 현재가 조회
def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]


# 5일 이동평균 조회
def get_maday5(ticker):
    """5일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=5)
    maday5 = df["close"].rolling(5).mean().iloc[-1]

    return maday5


# 15분 이동평균 조회
def get_mamin15(ticker):
    """15분 이동 평균선의 3회차 이동평균 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute5", count=3)
    mamin15 = df["close"].rolling(3).mean().iloc[-1]
    return mamin15


# 시장 시작시간 조회
def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time


# 매도 가격 타겟팅
def get_sell_price(ticker, k):
    """15분 이평선의 하락 변동성 돌파시 매도"""
    df = pyupbit.get_ohlcv(ticker, interval="minute15", count=1)
    sell_price = get_mamin15(ticker) - (df.iloc[0]["high"] - df.iloc[0]["low"]) * k
    return sell_price


# 노이즈 함수
def get_noised_coin():
    """노이즈 0.4이하인것 조회"""
    tickers = pyupbit.get_tickers(fiat="KRW")
    df = pd.DataFrame()
    for ticker in tickers:
        try:
            temp = pyupbit.get_ohlcv(ticker, interval="day", count=20)
            temp["ticker"] = ticker
            df = pd.concat([df, temp])
        except:
            pass
    df_noise = pd.DataFrame()
    for ticker in tickers:
        try:
            temp = df
            temp["noise"] = 1 - (
                absolute(df["open"] - df["close"]) / absolute(df["high"] - df["low"])
            )
            df_noise = pd.concat([df, temp])
        except:
            pass

    noised_coin = []

    for ticker in tickers:
        check = df_noise[df_noise["ticker"] == ticker]
        if check["noise"].mean() < 0.5:
            # print(ticker, check['noise'].mean())
            noised_coin.append(ticker)
    return noised_coin


# 노이즈가 포함된 df 출력
def get_noised_df():
    """노이즈 0.4이하인것 조회"""
    tickers = pyupbit.get_tickers(fiat="KRW")
    df = pd.DataFrame()
    for ticker in tickers:
        try:
            temp = pyupbit.get_ohlcv(ticker, interval="day", count=20)
            temp["ticker"] = ticker
            df = pd.concat([df, temp])
        except:
            pass
    df_noise = pd.DataFrame()
    for ticker in tickers:
        try:
            temp = df
            temp["noise"] = 1 - (
                absolute(df["open"] - df["close"]) / absolute(df["high"] - df["low"])
            )
            df_noise = pd.concat([df, temp])
        except:
            pass
    return df_noise


# 시작 메세지 슬랙 전송
post_message(myToken, "#history", "autotrade start")

# 매수_매도 시작
fee = 0.0005
mycoin_li = []
noised_coin = get_noised_coin()
df_noise = get_noised_df()
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)
        # 9:00~9:10초사이에는 노이즈가 0.4이하인 코인 선정 업데이트
        if (
            start_time + datetime.timedelta(seconds=10)
            < now
            < end_time - datetime.timedelta(seconds=10)
        ):
            noised_coin = get_noised_coin()
            df_noise = get_noised_df()
        # 자동 매수, 매도 9:00 10초~다음날 8:59:50
        if (
            start_time + datetime.timedelta(seconds=10)
            < now
            < end_time - datetime.timedelta(seconds=10)
        ):
            for ticker in noised_coin:
                check = df_noise[df_noise["ticker"] == ticker]
                target_price = get_target_price(ticker, check["noise"].mean())
                maday5 = get_maday5(ticker)
                current_price = get_current_price(ticker)
                if target_price < current_price and maday5 < current_price:
                    krw = get_balance("KRW")
                    coin_budget = krw * ((1 - fee) / len(noised_coin))
                    if krw > 5000:
                        # 매수 단계
                        try:
                            buy_result = upbit.buy_market_order(ticker, coin_budget)
                            post_message(
                                myToken, "#history", "BTC buy : " + str(buy_result)
                            )
                        except Exception as e:
                            print(e)
                            post_message(myToken, "#history", e)

                        time.sleep(1)
                # 자동매도: 시가가 전 15분틱 3개의 이동평균의 노이즈만큼 감소 and 거래량 15분 틱 3개의 이동평균보다 낮을 시 매도
                sell_price = get_sell_price(ticker, check["noise"].mean())
                # coin_count = get_balance(ticker)
                if current_price < sell_price:
                    # sell_result = upbit.sell_market_order(ticker, coin_count)
                    sell_result = upbit.sell_market_order(ticker)
                    # mycoin_li = noised_coin
                    # mycoin_li = [i for i in mycoin_li if i not in ticker]
                    noised_coin = noised_coin.remove(ticker)
            # 청산 매도 8:59:50 10초~다음날 9:00:00
            else:
                try:
                    for ticker in mycoin_li:
                        # coin_count = get_balance(ticker)
                        sell_result = upbit.sell_market_order(ticker)
                        # sell_result = upbit.sell_market_order(ticker, coin_count)
                        post_message(
                            myToken, "#history", "BTC buy : " + str(sell_result)
                        )
                        time.sleep(1)
                except Exception as e:
                    print(e)
                    post_message(myToken, "#history", e)
    except Exception as e:
        print(e)
        post_message(myToken, "#histroy", e)
        time.sleep(1)
