import configparser
import datetime
import datetime as dt
from functools import reduce
import numpy as np
import pandas as pd
from pandas import DataFrame
from v20.errors import ResponseUnexpectedStatus, V20ConnectionError
import os
import json
import log
import prizing
from bd import saveReturns, get_returns
config = configparser.ConfigParser()
config.read('../config.properties')
periodicidad = config.get('configuracionGlobal', 'period')
possible_portfolio_currencies = (config.get('Trading', "possibles_portfolio_currencies")).split(" ")
class Portfolio():
    def __init__(self, robot):

        #portfolio best currency
        self.portfolio_currency = config.get("Trading", 'currency')

        self.robot = robot
        self.symbols=self.robot.symbols
        #dict to save the asset type of each symbol
        self.asset_types={symbol:type_ for type_ in self.robot.assets_config.keys() for symbol in  self.robot.assets_config[type_]}
        self.datetime_last_calculation_returns = self.robot.fechaInicio

        #log files
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        self.nombreFile = "logs/logs_portfolio" + now + ".txt"
        self.nombreFileException = "logs/logs_portfolioException" + now + ".txt"


        self.log = log.log()
        self.stock_frame = self.robot.stock_frame
        self.prizing = prizing.Prizing(robot)

        #to save all the trades closed today and update the daily returns in BD
        self.trades_closed_today= {}
        #to save all the trades open
        self.trades_open= {}

        #in each iteration we get the bid prizes to convert the money to the poertfolio currency and we save it heere to not recalculating multiples times in each iteration
        self.factores_conversion={}

        #calculates de symbol to convert the money to the currency of the portfolio
        self.__initialization_calculate_symbol_conversion()

        #inits the trades open today
        self.__init_trades_closed_today_trades_open()



    def __init_trades_closed_today_trades_open(self):
        for symbol in self.symbols:
            self.trades_open[symbol]=[]
            self.trades_closed_today[symbol] = []
            kwargs = {}
            kwargs["num_trades"] =  config.get("Trading", 'initial_trades_per_symbol_per_date')
            kwargs["symbol"] = symbol
            kwargs["state"] = "CLOSED"
            trades = [api.get_trades(**kwargs) for api in self.robot.apis]
            trades=reduce(lambda left ,right: left+right,trades)
            for trade in trades:
                    if trade.close_time.date() >= dt.datetime.today().date():
                        self.trades_closed_today[symbol].append(trade)

    def __initialization_calculate_symbol_conversion(self):
        self.convert_currencies={}
        for currency in possible_portfolio_currencies:
            self.convert_currencies[currency]={}
            quotes=[curr for curr in self.symbols if curr.split("_")[1]==currency]
            bases=[curr for curr in self.symbols if curr.split("_")[0]==currency]
            self.convert_currencies[currency]["quotes"]=quotes
            self.convert_currencies[currency]["bases"]=bases

    def calcularFactorConversion(self, symbol):
        kwargs = {}
        kwargs["periodicidad"] = periodicidad
        kwargs["num_bars"] = 1
        kwargs["price"] = config.get("Trading", 'bid_symbol')
        if symbol in self.robot.assets_config["forex"]:
            currency_aux=symbol.split("_")[0]
            if currency_aux==self.portfolio_currency:
                return 1
            symbol_as_quote=self.portfolio_currency+"_"+ currency_aux
            symbol_as_base=currency_aux+"_"+self.portfolio_currency
            if symbol_as_quote in self.convert_currencies[self.portfolio_currency]["bases"]:
                return 1/self.prizing.getLastBid(symbol_as_quote)
            else:
                return  self.prizing.getLastBid(symbol_as_base)
        return 1



    def add_trade_open(self, trade):
        symbol = trade.symbol
        if trade.id not in [t.id for t in self.trades_open[symbol]]:
            self.trades_open[symbol].append(trade)
            self.log.log(
                "Trade " + trade.id + " añadido a simbolo " + symbol + " initial units: " + str(trade.initial_units) +
                " current units: " + str(trade.current_units) + " actual profit: " + str(trade.unrealized_profit),
                self.nombreFile)

    def in_portfolio(self, symbol):
        if len(self.trades_open[symbol])>0:
                return True

        return False

    def in_portfolioCompra(self, symbol):
        if len([trade for trade in self.trades_open[symbol] if trade.current_units > 0]) > 0:
            return True

        return False

    def in_portfolioVenta(self, symbol):

        if len([trade for trade in self.trades_open[symbol] if trade.current_units < 0]) > 0:
                return True

        return False
    def set_positions(self):

        #calculate factors to convret to aour currency
        self.factores_conversion={symbol:self.calcularFactorConversion(symbol) for symbol in self.symbols}
        #delete trades closed yesterday
        for symbol in self.trades_closed_today.keys():
            for trade in self.trades_closed_today[symbol]:
                if trade.open_time.date() < dt.datetime.today().date():
                    self.trades_closed_today[symbol].remove(trade)

        #get new trades open that are not saved
        kwargs = {}
        kwargs["state"] = "OPEN"
        trades = self.robot.api_forex.get_trades(**kwargs)
        for trade in trades:
            self.add_trade_open(trade)

        #check if trades saved in open trades array have been closed
        for symbol in self.trades_open.keys():
            for trade_guardado in self.trades_open[symbol]:
                    trade = self.robot.api_forex.get_trade(trade_guardado.id)
                    if trade is not None:
                        if trade.state == "OPEN":
                            trade_guardado.current_units = trade.current_units
                            trade_guardado.unrealized_profit = trade.unrealized_profit

                        else:
                            self.trades_closed_today[symbol].append(trade)
                            self.trades_open[symbol].remove(trade_guardado)


    def is_profitable(self):
       profit=0
       trades_aux = self.trades_closed_today
       list_completed = [trade for symbol in trades_aux.keys() for trade in trades_aux[symbol]]
       for trade in  list_completed:
               profit += trade.realized_profit
       if profit > 0:
           return True
       else:
           return False

    def is_profitable_symbol(self, symbol):
        profit = 0
        for trade in self.trades_closed_today[symbol]:
                profit += trade.realized_profit
        if profit > 0:
            return True
        else:
            return False
    def portfolio_weights(self,stock_frame):
        return dict(stock_frame.groupby("symbol").amount.sum()/stock_frame.amount.sum())
        

    def portfolio_weights_today(self) -> dict:
        string_total = 'total'
        try:
            weights = {}


            # Grab the projected market value.
            projected_market_value_dict = self.market_value_today(self.symbols)

            # Loop through each symbol.
            for symbol in projected_market_value_dict:
                # Calculate the weights.
                if symbol != string_total:
                    if symbol in projected_market_value_dict.keys() and 'total_market_value' in projected_market_value_dict[symbol].keys():
                        weights[symbol] = projected_market_value_dict[symbol]['total_market_value'] / \
                                      projected_market_value_dict[string_total]['total_market_value']
                    else:
                        weights[symbol]=0

        except Exception as e:
            self.log.log(e, self.nombreFileException)
        return weights

    def portfolio_variance(self, weights: dict, covariance_matrix: DataFrame) -> dict:
        sorted_keys = list(weights.keys())
        sorted_keys.sort()

        sorted_weights = np.array([weights[symbol] for symbol in sorted_keys])
        portfolio_variance = np.dot(
            sorted_weights.T,
            np.dot(covariance_matrix, sorted_weights)
        )

        return portfolio_variance

    def __calculate_value(self, today_market_value, trades_list, key):

        today_market_value[key]['total_market_value'] = sum(
            [(trade.close_price *  abs(trade.initial_units) * self.factores_conversion[trade.symbol]) for trade in trades_list])
        today_market_value[key]['total_invested_capital'] = sum(
            [(trade.open_price * abs(trade.initial_units) * self.factores_conversion[trade.symbol]) for trade in trades_list])
        today_market_value[key]['total_profit_or_loss'] = sum([trade.realized_profit for trade in trades_list])
    def market_value_today(self, symbols):
            string_total="total"
            projected_value={}
            projected_value[string_total]={}
            for symbol in symbols:
                projected_value[symbol]={}
                self.__calculate_value( projected_value,self.trades_closed_today[symbol], symbol)

            list_completed = [trade for symbol in  self.trades_closed_today.keys() for trade in self.trades_closed_today[symbol]]
            projected_value[string_total]['total_positions'] = len([e for e,value in self.trades_closed_today.items() if len(value)>0 ])
            self.__calculate_value( projected_value, list_completed, string_total)
            profitable=[self.is_profitable_symbol(symbol) for symbol in self.symbols]
            projected_value[string_total]['number_of_profitable_positions'] =profitable.count(True)
            projected_value[string_total]['number_of_non_profitable_positions'] =profitable.count(False)
            return projected_value

    def get_trades_symbol_dataframe(self, trades):
        dataframe_returns = pd.DataFrame(columns=["profit", "amount", "time"])
        for trade in trades:
            dataframe_returns.loc[len(dataframe_returns), ["profit", "amount", "time"]] = \
                [trade.realized_profit, abs(trade.initial_units * self.factores_conversion[trade.symbol]), \
                 (trade.close_time - trade.open_time).seconds / 60]
        return dataframe_returns
    def get_trades_dataframe(self,trades):
        dataframe_returns = pd.DataFrame(columns=["date","symbol","profit", "amount", "time"])
        for trade in trades:
            dataframe_returns.loc[len(dataframe_returns), ["date","symbol","profit", "amount", "time"]] = \
                [trade.close_time.date(),trade.symbol,trade.realized_profit, abs(trade.initial_units * self.factores_conversion[trade.symbol]), \
                 (trade.close_time - trade.open_time).seconds / 60]
        return dataframe_returns

    def initial_save_returns(self):
        dataframe_final = pd.DataFrame(columns=["symbol", "date", "profit", "amount", "total_time"])
        dataframe_final.set_index(["symbol", "date"], inplace=True, drop=True)
        kwargs = {"state": "CLOSED", "num_trades":config.get('Trading',"initial_trades_per_symbol_per_date")}
        trades=[]
        for symbol in self.symbols:
            kwargs["symbol"]=symbol
            trades=trades+self.robot.api_forex.get_trades(**kwargs)
        dataframe_returns = self.get_trades_dataframe(trades)
        if len(dataframe_returns) > 0:
            dataframe_returns["amount"] = dataframe_returns.time * dataframe_returns.amount
            dataframe_returns_grouped=dataframe_returns.groupby(by=["symbol","date"])["profit","amount","time"].\
                apply(lambda x : x.astype(float).sum())
            dataframe_returns_grouped.rename(columns={"time":"total_time"},inplace=True)
            dataframe_returns_grouped["amount"]= dataframe_returns_grouped.amount/dataframe_returns_grouped.total_time
            saveReturns(dataframe_returns_grouped)

    def obtener_returns(self, simbolos: list):
        """
        Gets daily returns from the list of symbols and saves them in database

        @param simbolos: symbols to get the returns
        @return:
        """

        dataframe_final = pd.DataFrame(columns=["symbol","date", "profit", "amount","total_time"])
        dataframe_final.set_index(["symbol","date"],inplace=True,drop=True)
        for symbol in simbolos:
            self.log.log("Getting data of symbol " + str(symbol), self.nombreFile)
            try:
                trades = self.trades_closed_today[symbol]
                dataframe_returns =self.get_trades_symbol_dataframe(trades)
                if len(dataframe_returns) > 0:
                    dataframe_returns["time_count"]=dataframe_returns.time*dataframe_returns.amount
                    profit= dataframe_returns.profit.sum()
                    time=dataframe_returns.time.sum()
                    amonut=sum(dataframe_returns.time_count/time)
                    array=[profit,amonut,time]
                    dataframe_final.loc[(symbol,dt.datetime.today().date()),:]=array
            except   ResponseUnexpectedStatus as e:
                self.log.log(str(e), self.nombreFileException)
            except   V20ConnectionError as e:
                self.log.log(str(e), self.nombreFileException)

        if len(dataframe_final) > 0:
            saveReturns(dataframe_final)

            self.datetime_last_calculation_returns = datetime.datetime.now()
        self.log.log(self.trades_closed_today, self.nombreFile)

        return dataframe_final

    def portfolio_metrics(self):
        """Calculates different portfolio risk metrics using daily data.

                    Overview:
                    ----
                    To build an effective summary of our portfolio we will need to
                    calculate different metrics that help represent the risk of our
                    portfolio and it's performance. The following metrics will be calculated
                    in this method:

                    1. Standard Deviation of Percent Returns.
                    2. Covariance of Percent Returns.
                    2. Variance of Percent Returns.
                    3. Average Percent Return
                    4. Weighted Average Percent Return.
                    5. Portfolio Variance.

                    Returns:
                    ----
                    dict -- [description]

                    """

        try:
            stock_frame = get_returns()

            # Calculate the Daily Returns (%)
            stock_frame['returns_pct'] = stock_frame.apply(
                lambda row: 0 if row.amount == 0 else row.profit / row.amount, axis=1)
            stock_frame.fillna(0, inplace=True)

            stock_frame['returns_avg'] = stock_frame.groupby(
                "symbol")['returns_pct'].transform(lambda x: x.mean())
            # Calculate the Daily Returns (Standard Deviation)
            stock_frame['returns_std'] = stock_frame.groupby(
                "symbol")['returns_pct'].transform(lambda x: x.std())



            returns_cov = stock_frame.unstack(
                level=0, fill_value=0)['returns_pct'].cov()
            returns_corr = stock_frame.unstack(
                level=0, fill_value=0)['returns_pct'].corr()

            porftolio_weights = self.portfolio_weights(stock_frame)

            returns_avg = stock_frame.groupby(
                by='symbol',
                as_index=False,
                sort=True
            )['returns_avg'].tail(
                n=1
            ).to_dict()

            returns_std = stock_frame.groupby(
                by='symbol',
                as_index=False,
                sort=True
            )['returns_std'].tail(
                n=1
            ).to_dict()

            metrics_dict = {}


            portfolio_variance = self.portfolio_variance(
                weights=porftolio_weights,
                covariance_matrix=returns_cov
            )

            for index_tuple in returns_std:
                symbol = index_tuple[0]
                if symbol in porftolio_weights.keys():
                    metrics_dict[symbol] = {}
                    metrics_dict[symbol]['weight'] = porftolio_weights[symbol]
                    metrics_dict[symbol]['average_returns'] = returns_avg[index_tuple]
                    metrics_dict[symbol]['weighted_returns'] = returns_avg[index_tuple] * \
                                                               metrics_dict[symbol]['weight']
                    metrics_dict[symbol]['standard_deviation_of_returns'] = returns_std[index_tuple]
                    metrics_dict[symbol]['variance_of_returns'] = returns_std[index_tuple] ** 2
                    metrics_dict[symbol]['covariance_of_returns'] = returns_cov.loc[[
                        symbol]].to_dict()

            metrics_dict['portfolio'] = {}
            metrics_dict['portfolio']['variance'] = portfolio_variance

            return metrics_dict
        except ValueError as e:
            self.log.log(e, self.nombreFileException)
