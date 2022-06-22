from trade import Trade
from external_trading_api import External_api
import  oanda_api_requests.bars as bars ,oanda_api_requests.trades as trades
from entitites.entities import Trade_entity
import configparser
import pandas as pd
import v20
import datetime as dt
config = configparser.ConfigParser()
config.read('../config.properties')
hostname = (config.get('configuracionGlobal', "hostname"))
port = int(config.get('configuracionGlobal', "port"))
token = (config.get('configuracionGlobal', "apikey"))
account = (config.get('configuracionGlobal', "accountNumber"))
ssl = True if (config.get('configuracionGlobal', "ssl")) == "True" else False
datetime_format = (config.get('configuracionGlobal', "datetime_format"))
class Oanda_trading_api(External_api):
    def __init__(self):
        self.api = v20.Context(
            hostname,
            port,
            ssl,
            application="sample_code",
            token=token,
            datetime_format=datetime_format
        )
        self.account = account

    def get_data(self,stock_frame: pd.DataFrame, symbol: str, **kwargs):
        """


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
        bars.get_data(self.api,stock_frame, symbol, **kwargs)

    def bid_ask(self,symbol: str, tipo: str) -> float:
        """
         Returns last bid or ask of symbol.


        :param symbol: Symbol to get bid or ask
        :param tipo: "bid" or "ask"
        """
        return bars.bid_ask(self.api,self.account,symbol,tipo)

    def get_last_rows(self,stock_frame: pd.DataFrame, symbol: str, tiempo: dt.datetime,
                      dataframe_symbol: pd.DataFrame, **kwargs):
        """


        :param stock_frame: dataframe with all symbols
        :param tiempo: datetime of last bar
        :param dataframe_symbol: dataframe with data from this symbol

        kwargs:
            period:
                Period to get bars (str)

            price:
                "B" (bid)  or "A" (ask) (str)

            symbol:
                forex pair (str)

            from_time:
               Later time to get bars from (dt.datetime.timestamp)
        """
        bars.get_last_rows(self.api,stock_frame, symbol, tiempo, dataframe_symbol, **kwargs)


    def get_trades(self,**kwargs)-> list:
        """


           :return: list of Trade_entity
           :rtype: list

           kwargs:
            num_trades (optional):
                Number of trades to get from the external API (must be all current day trades) (int)

            symbol (optional):
                Symbol to get trades of (str)

            state:
                "OPEN" or "CLOSED"
           """
        trades_aux=trades.get_trades(self.api,self.account,**kwargs)
        return [Trade_entity(trade_aux.instrument,trade_aux) for trade_aux in trades_aux]

    def get_trade(self, trade: str)-> Trade_entity:
        """

               :param trade: trade ID
               :return : Trade entity
               """
        trade_aux=trades.get_trade(self.api,self.account,trade)
        return Trade_entity(trade_aux.instrument,trade_aux)

    def operate(self,trade_handler: Trade, symbol: str, **kwargs)-> Trade_entity or None:
        """

        :param trade_handler:  Trade class instance to log info
        :param symbol: forex pair to operate
        :return: trade information
         kwargs:
            type:
                Type of order  (str)
            units:
                number of units to buy or sell (int)

            takeProfit (optional):
                take profit value (float)

            stopLoss (optional):
                stop loss value (float)

        """
        trade_aux=trades.operate(self.api,self.account,trade_handler, symbol, **kwargs)
        if trade_aux is not None:
            return Trade_entity(trade_aux.instrument, trade_aux)
        else:
            return None

    def close_trade(self,trade_handler: Trade, symbol: str, tradeId: str, **kwargs):
        """

            :param tradeId: id of trade to close
            :param trade_handler: Trade class instance to log info
            :param symbol: forex pair to operate

            kwargs:
                units:
                    number of units to buy or sell

            """
        trades.close_trade(self.api, self.account, trade_handler, symbol, tradeId,**kwargs)
