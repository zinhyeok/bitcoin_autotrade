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
'''
f = open("upbit.txt")
lines = f.readlines()
access = lines[0].strip()
secret = lines[1].strip()
f.close()
'''

# Upbit class instance, object 만드는 과정
access = ""
secret = ""

upbit = pyupbit.Upbit(access, secret)

# slack에 메세지 봇 추가


def post_message(token, channel, text):
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + token},
        data={"channel": channel, "text": text},
    )
    print(response)


myToken = "slackbot token"


# 함수 모음

# 매수 목표가 조회
def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    try:
        df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
        target_price = (
            df.iloc[0]["close"] + (df.iloc[0]["high"] - df.iloc[0]["low"]) * k
        )
    except:
        target_price = NaN

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


# 3일 이동평균 조회
def get_maday3(ticker):
    """3일 이동 평균선 조회"""
    try:
        df = pyupbit.get_ohlcv(ticker, interval="day", count=3)
        maday3 = df["close"].rolling(3).mean().iloc[-1]
    except:
        maday3 = NaN

    return maday3


# 15분 이동평균 조회
def get_mamin15(ticker):
    """15분 이동 평균선의 3회차 이동평균 조회"""
    try:
        df = pyupbit.get_ohlcv(ticker, interval="minute5", count=3)
        mamin15 = df["close"].rolling(3).mean().iloc[-1]
    except:
        mamin15 = NaN

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
    try:
        df = pyupbit.get_ohlcv(ticker, interval="minute15", count=1)
        sell_price = get_mamin15(
            ticker) - (df.iloc[0]["high"] - df.iloc[0]["low"]) * k
    except:
        sell_price = NaN

    return sell_price


# 노이즈 함수

# 노이즈 코인 리스트로 반환
def get_noised_coin(tickers):
    """3일 노이즈 df에 추가 + 0.5아래인 값 분류"""
    df = pd.DataFrame()
    for ticker in tickers:
        try:
            temp = pyupbit.get_ohlcv(ticker, interval="day", count=3)
            temp["ticker"] = ticker
            df = pd.concat([df, temp])
        except:
            pass
    # 결측치 데이터 삭제
    df.dropna(inplace=True)

    df_noise = pd.DataFrame()
    for ticker in tickers:
        try:
            temp = df
            temp["noise"] = 1 - (
                absolute(df["open"] - df["close"]) /
                absolute(df["high"] - df["low"])
            )
            df_noise = pd.concat([df, temp])
        except:
            pass
    df_noise.dropna(inplace=True)

    noised_coin = []

    for ticker in tickers:
        check = df_noise[df_noise["ticker"] == ticker]
        if check["noise"].mean() < 0.5:
            # print(ticker, check['noise'].mean())
            noised_coin.append(ticker)

    return noised_coin


# 노이즈가 포함된 df 출력


def get_noised_df(tickers):
    """노이즈 0.5이하인것 조회"""
    #tickers = pyupbit.get_tickers(fiat="KRW")
    df = pd.DataFrame()
    for ticker in tickers:
        try:
            temp = pyupbit.get_ohlcv(ticker, interval="day", count=3)
            temp["ticker"] = ticker
            df = pd.concat([df, temp])
            df.dropna(inplace=True)
        except:
            pass

    df_noise = pd.DataFrame()
    for ticker in tickers:
        try:
            temp = df
            temp["noise"] = 1 - (
                absolute(df["open"] - df["close"]) /
                absolute(df["high"] - df["low"])
            )
            df_noise = pd.concat([df, temp])

        except:
            temp = df
            temp["noise"] = NaN
            df_noise = pd.concat([df, temp])

    df_noise.dropna(inplace=True)
    return df_noise


# 매수, 매도의 target df만들기(기존 방식으로는 내가 원하는 코인을 원하는 가격에 매수 불가: 자료구조 문제) -> df로 변경 해결


def get_target_df(tickers):
    target_df = pd.DataFrame(
        columns=["coin", "target_price", "maday3", "sell_price", "k"]
    )
    for coin in tickers:
        df_noise = get_noised_df(tickers)
        check = df_noise[df_noise["ticker"] == coin]
        target_coin = coin
        k = check["noise"].mean()
        target_price = get_target_price(coin, k)
        maday3 = get_maday3(coin)
        sell_price = get_sell_price(coin, k)
        # DataFrame에 특정 정보를 이용하여 data 채우기
        target_df = target_df.append(
            pd.DataFrame([[target_coin, target_price, maday3, sell_price, k]], columns=["coin", "target_price", "maday3", "sell_price", "k"],
                         ), ignore_index=True,)
    target_df.dropna(inplace=True)

    return target_df


# 매도 가격 5분마다 업데이트
def get_updateSell_price(df, ticker, k):
    try:
        df = df
        df["sell_price"] = df["sell_price"].map(get_sell_price(ticker, k))
    except:
        df = df
        df["sell_price"] = NaN

    return df

# 주문 채결 확인 알고리즘


def check_order(ticker):
    buy_unconcluded = upbit.get_order()
    df = pd.DataFrame(buy_unconcluded)
    unconcluded_coin = df['market'].values.tolist()
    if ticker in unconcluded_coin:
        uuid = upbit.get_oder('uuid')
        upbit.cancel_order(uuid)
        return 1
    else:
        return 0

# 매수 알고리즘(약 11초 delay 발생)


def buy_coin(ticker, price):
    upbit.buy_market_order(ticker, price)
    time.sleep(1)
    check_buy = check_order(ticker)
    if check_buy == 0:
        post_message(myToken,
                     "#history",
                     "코인 매수 : " + str(ticker)
                     )
        return 0
    while(check_buy == 1):
        upbit.buy_market_order(ticker, price)
        time.sleep(10)
        check_buy = check_order(ticker)
        if check_buy == 0:
            post_message(
                myToken,
                "#history",
                "코인 매수 : " + str(ticker)
            )
            break
    return 0

# 매도 알고리즘(약 11초 delay 발생)


def sell_coin(ticker, balance):
    upbit.sell_market_order(ticker, balance)
    time.sleep(1)
    check_sell = check_order(ticker)
    if check_sell == 0:
        post_message(
            myToken,
            "#history",
            "코인 매도 : " + str(ticker)
        )
        return 0
    while(check_sell == 1):
        upbit.sell_market_order(ticker, balance)
        time.sleep(10)
        check_sell = check_order(ticker)
        if check_sell == 0:
            post_message(
                myToken,
                "#history",
                "코인 매도 : " + str(ticker)
            )
            break
    return 0

# 거래량 상위 50개만 가져오기


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
        'ticker', sort=False).head(50)
    sort_coin50 = df_sort_top50['ticker'].values.tolist()
    return sort_coin50


# 병렬 처리 추가 할것!
# 매수_매도 시작
noised_coin = None
target_df = None
tickers = pyupbit.get_tickers(fiat="KRW")
KST = pytz.timezone('Asia/Seoul')
# 시작 메세지 슬랙 전송
post_message(myToken, "#history", "시스템 시작")
print("Trade System Start")
print(get_sort50(tickers))

sort_coin50 = ['KRW-BTT', 'KRW-XEC', 'KRW-BTC']
current_coin = []
noised_coin = get_noised_coin(sort_coin50)
target_df = get_target_df(noised_coin)
print(target_df)
target_coin = target_df[0].values.tolist()
print(target_coin)
A = False
while(A == True):
    try:
        now = datetime.datetime.now(KST)
        start_time = datetime.datetime(now.year, now.month, now.day, 9, 00, 00)
        end_time = start_time + datetime.timedelta(days=1)
        start_time = KST.localize(start_time)
        end_time = KST.localize(end_time)
        # 9:00~9:01 10초사이에는 노이즈가 0.4이하인 코인 선정 업데이트 & 수익률 업데이트 &목표가 seting
        if (
            start_time < now < start_time + datetime.timedelta(seconds=10)
            or target_df is None
        ):
            fee = 0.0005
            try:
               # tickers = pyupbit.get_tickers(fiat="KRW")
               # sort_coin50 = get_sort50(tickers)
                sort_coin50 = ['KRW-BTT', 'KRW-XEC', 'KRW-MFT', 'KRW-MBL', 'KRW-TRX', 'KRW-TFUEL', 'KRW-QKC', 'KRW-DOGE', 'KRW-SC', 'KRW-AHT', 'KRW-VET', 'KRW-MVL', 'KRW-XRP', 'KRW-STMX', 'KRW-RFR', 'KRW-MED', 'KRW-POWR', 'KRW-ORBS', 'KRW-ANKR', 'KRW-IQ', 'KRW-JST', 'KRW-BORA', 'KRW-SNT', 'KRW-ZIL', 'KRW-MANA', 'KRW-META', 'KRW-ONG', 'KRW-SSX', 'KRW-WAXP', 'KRW-ICX', 'KRW-STPT', 'KRW-CHZ', 'KRW-XLM', 'KRW-WEMIX', 'KRW-ADA', 'KRW-HBAR', 'KRW-ZRX', 'KRW-UPP', 'KRW-HUM', 'KRW-MOC', 'KRW-AERGO', 'KRW-FCT2', 'KRW-STEEM', 'KRW-ONT', 'KRW-THETA', 'KRW-ALGO', 'KRW-SXP',
                               'KRW-ARDR', 'KRW-POLY', 'KRW-STX', 'KRW-KNC', 'KRW-CRO', 'KRW-EOS', 'KRW-ELF', 'KRW-WAVES', 'KRW-FLOW', 'KRW-CVC', 'KRW-SBD', 'KRW-GLM', 'KRW-MLK', 'KRW-DAWN', 'KRW-1INCH', 'KRW-ENJ', 'KRW-GRS', 'KRW-KAVA', 'KRW-SRM', 'KRW-NEO', 'KRW-HIVE', 'KRW-PUNDIX', 'KRW-STORJ', 'KRW-IOTA', 'KRW-GAS', 'KRW-ARK', 'KRW-AXS', 'KRW-NEAR', 'KRW-MTL', 'KRW-AQT', 'KRW-XTZ', 'KRW-STRAX', 'KRW-LSK', 'KRW-ETC', 'KRW-OMG', 'KRW-CBK', 'KRW-TON', 'KRW-LINK', 'KRW-DOT', 'KRW-SOL', 'KRW-AVAX', 'KRW-REP', 'KRW-STRK', 'KRW-BTG', 'KRW-ETH', 'KRW-BSV', 'KRW-LTC', 'KRW-AAVE', 'KRW-BTC']
                current_coin = []
                noised_coin = get_noised_coin(sort_coin50)
                target_df = get_target_df(noised_coin)

                post_message(
                    myToken, "#history", "현재 잔고는: " +
                    str(upbit.get_balance("KRW"))
                )
                target_coin = target_df['coin'].values.tolist()
                print(target_coin)

                print("set end")
                post_message(myToken, "#history", "세팅 완료 시간: " + str(now))
                post_message(myToken, "#history", "타깃은: " +
                             " ".join(target_coin))

            except:
                post_message(myToken, "#history", "세팅 실패")
                print("set fail")
                target_df = None
        # 자동 매수, 매도 9:00 10초~다음날 8:59분
        elif (
            start_time + datetime.timedelta(seconds=10)
            < now
            < end_time - datetime.timedelta(minutes=1)
            and target_df is not None
        ):
            print("...................")
            if noised_coin is not None:
                for ticker in noised_coin:
                    target_price = target_df.loc[ticker, "target_price"]
                    maday3 = target_df.loc[ticker, "maday3"]
                    current_price = get_current_price(ticker)
                    # 이동평균선보다 가격이 높고, 변동성 돌파 가격보다도 높을 시 매수
                    if target_price < current_price and maday3 < current_price:
                        krw = get_balance("KRW")
                        coin_budget = int(krw * ((1 - fee) / len(noised_coin)))
                        # 매수 단계
                        try:
                            buy_result = buy_coin(ticker, coin_budget)
                            if buy_result == 0:
                                noised_coin.remove(ticker)
                                current_coin.append(ticker)

                        except Exception as e:
                            print("buy error: {}".format(e))
                            post_message(myToken, "#history",
                                         "매수에러: " + str(e))
                            if str(e) in noised_coin:
                                noised_coin.remove(e)
                            else:
                                pass
                        time.sleep(1)

                # 자동매도: 시가가 전 15분틱 3개의 이동평균의 노이즈만큼 감소 and 거래량 15분 틱 3개의 이동평균보다 낮을 시 매도 + 내가 현재 보유중인 코인만 매도
                # 매도 후에는 오늘 보유리스트에서 제거
                if current_coin is not None:
                    for ticker in current_coin:
                        target_df = get_updateSell_price(target_df, ticker, k)
                        k = target_df.loc[ticker, "k"]
                        sell_price = target_df.loc[ticker, "sell_price"]
                        coin_count = get_balance(ticker)

                        if sell_price is NaN:
                            sell_price = current_price * 100

                        if current_price < sell_price and ticker in current_coin:
                            try:
                                sell_result = sell_coin(ticker, coin_count)
                                if sell_result == 0:
                                    current_coin.remove(ticker)
                            except Exception as e:
                                print("sell error: {}".format(e))
                                post_message(myToken, "#histroy",
                                             "매도 에러:" + str(e))
                        time.sleep(280)

        # 모두 청산 매도 다음날 8:59:00~ 9:00:00
        else:
            try:
                if current_coin is not None:
                    for ticker in current_coin:
                        coin_count = get_balance(ticker)
                        # sell_result = upbit.sell_market_order(ticker)
                        sell_result = sell_coin(ticker, coin_count)
                        if sell_result == 0:
                            current_coin.remove(ticker)

                        time.sleep(1)

            except Exception as e:
                print("all sell error: {}".format(e))
                post_message(myToken, "#history", "청산 에러:" + str(e))

    except Exception as e:
        print("auto set error: {}".format(e))
        post_message(myToken, "#histroy", "전체 코드 에러:" + str(e))
        if str(e) in tickers:
            tickers.remove(e)
        else:
            pass
        time.sleep(1)
