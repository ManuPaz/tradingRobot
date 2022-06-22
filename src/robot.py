import configparser
import datetime as dt
import json
import threading
import operator
from datetime import datetime
from v20.errors import V20Timeout,V20ConnectionError
import indicators
import log
import prizing
import stock_frame
import oanda_api_requests.oanda_api_exernal_datasource as  oanda_api_exernal_datasource
import os
config = configparser.ConfigParser()
config.read('../config.properties')
fechaIni = (config.get('configuracionGlobal', "fechaIni"))
dir_results = "../results/"
if not os.path.isdir(dir_results):
    os.mkdir(dir_results)

class Robot():
    @property
    def symbols(self):
        return self.__symbols
    @property
    def portfolio(self):
        return self.__portfolio

    @portfolio.setter
    def portfolio(self, portfolio):
        self.__portfolio = portfolio
        try:
            # update positions info
            self.__portfolio.set_positions()

        except  V20Timeout as e:
            self.log.log(e, self.nombreFile)



    @property
    def trades_module(self):
        return self.__trades_module

    @trades_module.setter
    def trades_module(self, trades):
        self.__trades_module = trades
        for s in self.__symbols:
            self.__trades_module.close_trades(s)

    @property
    def trading_config(self):
        return self.__trading_config

    @trading_config.setter
    def trading_config(self, trading_config):
        self.__trading_config = trading_config

    @property
    def assets_config(self):
        return self.__assets_config

    @property
    def api_forex(self) ->  oanda_api_exernal_datasource.Oanda_trading_api:
        return self.__api_forex

    def __init_indicators(self):
        self.log.log("Indicators: ", self.nombreFile)
        for dato in self.__trading_config["indicators"]:
            self.log.log(dato, self.nombreFile)
            func = getattr(self.indicators, dato["name"])
            func(dato["period"], column_name=dato["column"])


        self.log.log("Strategies: ", self.nombreFile)
        for dato in self.__trading_config["strategies"]:
            self.log.log(dato, self.nombreFile)
            operadorSell = None
            operadorBuy = None
            if dato["condition_sell"] == "menorigual":
                operadorSell = operator.lt
            elif dato["condition_sell"] == "mayorigual":
                operadorSell = operator.gt
            if dato["condition_buy"] == "menorigual":
                operadorBuy = operator.lt
            elif dato["condition_buy"] == "mayorigual":
                operadorBuy = operator.gt
            if "name" in dato.keys():
                self.columns_used_trading.append(dato["name"])
                self.indicators.set_indicator_signal(dato["name"], buy=dato["buy"], sell=dato["sell"],
                                                     condition_sell=operadorSell,
                                                     condition_buy=operadorBuy, symbols=dato["symbols"])
            else:
                self.columns_used_trading.append(dato["name1"])
                self.columns_used_trading.append(dato["name2"])
                self.indicators.set_indicator_signal_compare(dato["name1"], dato["name2"],
                                                             condition_sell=operadorSell,
                                                             condition_buy=operadorBuy, symbols=dato["symbols"])



    def __init__(self, periodicidad):
        self.__api_forex =  oanda_api_exernal_datasource.Oanda_trading_api()
        self.nombreFile = "logs/logs_run" + str(dt.datetime.now().date()) + ".txt"
        self.nombreFileExeption = "logs/logs_runException" + str(dt.datetime.now().date()) + ".txt"
        self.log = log.log()
        self.columns_used_trading=[]
        self.periodicidad = periodicidad
        self.fechaInicio = datetime.now()
        self.fechaInicio = datetime.strptime(fechaIni, "%Y-%m-%d")
        self.lastTime = None
        self.prizing = prizing.Prizing(self)
        self.stock_frame = stock_frame.StockFrame(self, config.get('configuracionGlobal', "past_bars"))
        self.indicators = indicators.Indicators(self.stock_frame.stock_frame, self)
        file = open('../assets/trading_config.json', 'r')
        self.__trading_config = json.load(file)
        file = open('../assets/assets_config.json', 'r')
        self.__assets_config = json.load(file)
        self.__symbols = [symbol for key in self.__assets_config.keys() for symbol in self.__assets_config[key]]
        [self.stock_frame.addSymbol(i, self.periodicidad) for i in self.__symbols]
        self.__init_indicators()
        self.__portfolio = None
        self.__trades_module = None
        self.apis = [self.api_forex]
        self.symbols_being_trading=[]
        #lock to operate
        self.operations_lock=threading.Lock()

    def log_info(self):
        self.log.log("NUmber of trades open: {}, number of trades closed today {}".format(
            sum([len(self.portfolio.trades_open[symbol]) for symbol in self.symbols]),
            sum([len(self.portfolio.trades_closed_today[symbol]) for symbol in self.symbols])), self.nombreFile,
            printed=True)
        self.log.log((self.stock_frame.stock_frame.loc[:, ["symbol", "time"] + self.columns_used_trading].tail(
            len(self.__symbols))), self.nombreFile,
            printed=True)

    def __operate(self, signals):

        for signal in signals:
            if (signal[0] == "buys"):
                self.log.log("buy {}".format(list(signal[1].index)), self.nombreFile)
                symbols_to_operate = signal[1].reset_index(level=0)["symbol"]

                for symbol_to_operate in symbols_to_operate:
                    if self.__portfolio.in_portfolioVenta(symbol_to_operate):
                        self.__trades_module.close_trades(symbol_to_operate)
                    elif not self.__portfolio.in_portfolioCompra(symbol_to_operate):
                        self.__trades_module.market_order("forex", symbol_to_operate, "buy",
                                                          stop_loss=self.__trading_config["trades"]["stop_loss"][
                                                              symbol_to_operate],
                                                          take_proffit=self.__trading_config["trades"]["take_profit"][
                                                              symbol_to_operate],
                                                          units=self.__trading_config["trades"]["units"][
                                                              symbol_to_operate])
            if (signal[0] == "sells"):
                self.log.log("sell {}".format(list(signal[1].index)), self.nombreFile)
                symbols_to_operate = signal[1].reset_index(level=0)["symbol"]

                for symbol_to_operate in symbols_to_operate:
                    if self.__portfolio.in_portfolioCompra(symbol_to_operate):
                        self.__trades_module.close_trades(symbol_to_operate)
                    elif not self.__portfolio.in_portfolioVenta(symbol_to_operate):
                        self.__trades_module.market_order("forex", symbol_to_operate, "sell",
                                                          stop_loss=self.__trading_config["trades"]["stop_loss"][
                                                              symbol_to_operate],
                                                          take_proffit=self.__trading_config["trades"]["take_profit"][
                                                              symbol_to_operate],
                                                          units=self.__trading_config["trades"]["units"][
                                                              symbol_to_operate])

    def run(self):
        #time to compute iteration time
        time_start = dt.datetime.now()
        #if we can
        operate=True

        #the series and signals updates must be executed synchronously
        #it will be the normal sitution, buy if a big amount of symbols, indicators and past bars is used with a low period (such as 15 seconds) it could not happen
        #so this must be insured using locks
        #we check if the operation is blocked by the previus iteration
        #we call the Lock.adquiere method no blocking, so if it is block it returns False and if not it blocks and returns True
        #if it is blocked  skip this iteration because it is in the previus one and try again in the nexet call
        not_blocked=self.operations_lock.acquire(blocking=False)
        if not_blocked:
            for e in self.stock_frame.symbols:
                try:
                    self.stock_frame.addRow(e, self.periodicidad)
                except  (V20Timeout, V20ConnectionError) as e:
                    self.log.log(e, self.nombreFile)
                    operate = False
            try:
                #update positions info
                self.__portfolio.set_positions()

            except  (V20Timeout,V20ConnectionError) as e:
                self.log.log(e,self.nombreFile)
                operate=False

            self.indicators.refresh()
            signals = self.indicators.check_signals()
            self.log_info()

        # now lock is realised. Trading operations are done without blocking (only blocking the symbl being traded)
        # but traing operations are done only if pervius part was executed so there is new info to trade
        if not_blocked:
            self.operations_lock.release()


        if operate and not_blocked:
            #we trade in another thread to allow the robot to run each iteration quicky
            #in that thread it will block the symbol in which operates, and if it will pass any symbol that is bloacked
            #so the maximun number of threads will be running will be the same as the number of symbols, becasuse any other thread will end instantanly
            #but that is a not probable case
            #it is usefull to use trades because the most costly operations in the trade operation are IO operations (call to the network API using requests library)
            thread=threading.Thread(target= self.__operate,args=(signals,))
            thread.start()

        self.log.log("Run finished, duration: {} seconds, operate={}, blocked={}, number of threads working {}".format((dt.datetime.now() - time_start).seconds,operate,not not_blocked,threading.active_count()),
                     self.nombreFile,printed=True)

    def portfolio_operations(self):
        tiempo1 = dt.datetime.now()
        self.__portfolio.set_positions()
        self.__portfolio.obtener_returns(self.__symbols)
        weights=self.__portfolio.portfolio_weights_today()
        metrics=self.__portfolio.portfolio_metrics()
        with open(dir_results+"weights_today"+str(dt.date.today())+".json","w") as file:
            json.dump(weights,file)
        with open(dir_results + "metrics" + str(dt.date.today()) + ".json","w") as file:
            json.dump(metrics,file)

        self.log.log(
            "Portfolio calculation finished, duration: {} seconds".format((dt.datetime.now() - tiempo1).seconds),
            self.nombreFile,
            printed=True)
