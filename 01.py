# pyupbit API
import pyupbit

# tickers = pyupbit.get_tickers(fiat="KRW")
# print(tickers)

# df = pyupbit.get_ohlcv("KRW-BTC", "minute3")
# print(df)

# 빈데이터, 실시간데이터는 잘못된 데이터를 받는 경우가 많음 , 12시전에
# 웹소캣으로 초단위로 받아올 수 있음?? 제약조건?

# 현재가 불러오기
# krw_tickers = pyupbit.get_tickers(fiat="KRW")
# prices = pyupbit.get_current_price(krw_tickers)

# for k, v in prices.items():
#     print(k, v)

# #호가보기
# import pprint

# orderbooks = pyupbit.get_orderbook("KRW-BTC")
# pprint.pprint(orderbooks)

# # 매도 호가의 총잔량? oderbook['']'total_ask_size': 0.98744208,'total_bid_size': 2.54255965}
