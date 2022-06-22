import datetime as dt

import pandas as pd
import v20
import configparser
config = configparser.ConfigParser()
config.read('../config.properties')
def bid_ask(api: v20.Context, account: str, symbol:str, tipo: str) -> float:
    """
     Returns last bid or ask of symbol.

    :param api: API to call to get the candles
    :param account: account id
    :param symbol: Symbol to get bid or ask
    :param tipo: "bid" or "ask"
    """
    atributes={config.get("Trading", 'ask_symbol'):"closeoutAsk",config.get("Trading", 'bid_symbol'):"closeoutBid"}
    response = api.pricing.get(account, instruments=symbol)
    return getattr(response.get("prices", 200)[0],atributes[tipo])

def get_data(api: v20.Context, stock_frame:pd.DataFrame,symbol: str, **kwargs ):
    """

    :param api: API to call to get the candles
    :param stock_frame: dataframe with all symbols
    :param symbol: forex pair

    kwargs:
        period:
            Period to get bars (str)

        price:
            "B" (bid)  or "A" (ask) (str)

        num_bars:
            NUmber of bars to get (int)

    """
    bid_ask={"A":"ask","B":"bid"}
    kwargs["granularity"] = kwargs["period"]
    kwargs["count"] = kwargs["num_bars"]
    response = api.instrument.candles(symbol, **kwargs)
    candles = response.get("candles", 200)
    candles = candles[0:-1]
    lenght_data = len(stock_frame)
    for row in candles:
        prize=getattr(row, bid_ask[kwargs["price"]])
        row_values = [symbol, dt.datetime.fromtimestamp(float(row.time)), prize.o, prize.c, prize.h, prize.l,
                      row.volume]
        stock_frame.loc[lenght_data, ['symbol', 'time', 'open', 'close', 'high', 'low', 'volume']] = row_values
        lenght_data = lenght_data + 1
def get_last_rows(api: v20.Context, stock_frame:pd.DataFrame, symbol: str, tiempo: dt.datetime,
                  dataframe_symbol: pd.DataFrame, **kwargs):
    """

    :param api: API to call to get the candles
    :param stock_frame: dataframe with all symbols
    :param symbol: forex pair
    :param tiempo: datetime of last bar
    :param dataframe_symbol: dataframe with data from this symbol

    kwargs:
        period:
            Period to get bars (str)

        price:
            "B" (bid)  or "A" (ask) (str)

        from_time:
           Later time to get bars from (dt.datetime.timestamp)
    """

    kwargs["granularity"] = kwargs["period"]
    kwargs["fromTime"] = kwargs["from_time"]
    response = api.instrument.candles(symbol, **kwargs)
    candles = response.get("candles", 200)
    bid_ask = {"A": "ask", "B": "bid"}
    candles = candles[0:-1]
    length_data = len(stock_frame)

    eliminados = 0
    for row in candles:
        if tiempo != dt.datetime.fromtimestamp(float(row.time)):
            prize = getattr(row, bid_ask[kwargs["price"]])
            row_values = [symbol, dt.datetime.fromtimestamp(float(row.time)), prize.o, prize .c, prize .h, prize .l,
                          row.volume]

            stock_frame.loc[length_data, ['symbol', 'time', 'open', 'close', 'high', 'low', 'volume']] = row_values
            length_data = length_data + 1
            eliminados = eliminados + 1

    if eliminados != 0:
        to_delete = dataframe_symbol.index[0:eliminados]
        stock_frame.drop(to_delete, axis=0, inplace=True)

        stock_frame.reset_index(drop=True, inplace=True)
