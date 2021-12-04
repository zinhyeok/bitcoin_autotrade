import pyupbit
import numpy as np

# ohlcv: 시가, 고가, 저가, 종가, 거래량, count: 불러울 일자
df = pyupbit.get_ohlcv("KRW-BTC", count=7)

##전략 시작(변동성 돌파전략)
# 변동폭 * k 계산
df["range"] = (df["high"] - df["low"]) * 0.5
# 현재 시가에서 어제 기준 range인 .shift(1) 만큼 오르면 target
df["target"] = df["open"] + df["range"].shift(1)

fee = 0.05
# 수익율 계산기 ror, np.where(조건문: 구매시, 종가(판매가)/목표가, 1 거짓일때 -> 거래 미발생시)
df["ror"] = np.where(df["high"] > df["target"], df["close"] / df["target"] - fee, 1)
# 누적 수익율
df["hpr"] = df["ror"].cumprod()
# drop down: 누적 최대 수익율과 현재 누적 수익율의 차이 dd
df["dd"] = (df["hpr"].cummax() - df["hpr"]) / df["hpr"].cummax() * 100

# 최대 낙폭 MDD
print("MDD(%): ", df["dd"].max())
df.to_excel("dd.xlsx")
