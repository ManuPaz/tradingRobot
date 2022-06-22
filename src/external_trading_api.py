
import pandas as pd
import datetime as dt
from abc import abstractmethod
from  trade import Trade
from entitites.entities import Trade_entity
class External_api():


    @abstractmethod
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
        pass

    @abstractmethod
    def bid_ask(self,symbol: str, tipo: str) -> float:
        """
         Returns last bid or ask of symbol.


        :param symbol: Symbol to get bid or ask
        :param tipo: "bid" or "ask"
        """
        pass

    @abstractmethod
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

    @abstractmethod
    def get_trades(self,**kwargs)->list:
        """

            :
           :return: list of Trade_entity

           kwargs:
            num_trades (optional):
                Number of trades to get from the external API (must be all current day trades) (int)

            symbol (optional):
                Symbol to get trades of (str)
            state:
                "OPEN" or "CLOSED"

           """
        pass
    @abstractmethod
    def get_trade(self,trade: str)->Trade_entity:
        """

               :param trade: trade ID
               :return : trade corresponding to that trade ID
               """

    @abstractmethod
    def operate(self, trade_handler: Trade, symbol:str, **kwargs):
        """

        :param trade_handler:  Trade class instance to log info
        :param symbol: forex pair to operate
        :return : trade information
        :rtype: Trade_entity or None

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
        pass

    @abstractmethod
    def close_trade(self, trade_handler: Trade, symbol: str, tradeId: str, **kwargs):
        """

            :param tradeId: id of trade to close
            :param trade_handler: Trade class instance to log info
            :param symbol: forex pair to operate

            kwargs:
                units:
                    number of units to buy or sell

            """
        pass

