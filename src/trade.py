from datetime import datetime
import log
import collections
from entitites.entities import Trade_entity
class Trade():
    def __init__(self, robot):
        self.robot = robot
        self.log = log.log()
        now = datetime.now().strftime("%Y-%m-%d")
        self.nombreFile = "logs/logs_trade" + now + ".txt"
        self.nombreFileException = "logs/logs_tradeException" + now + ".txt"

    def market_order(self, asset_type, symbol, side, units, stop_loss=0, take_proffit=0):


        #to make the symbols we are trading thread standard_deviation_of_returns
        self.robot.symbols_being_trading.append(symbol)
        counter=collections.Counter(self.robot.symbols_being_trading)
        if counter[symbol]==1:
            try:
                decimales = (len(str(self.robot.prizing.getLastBid(symbol)).split(".")[1]))

                pips = 10 * 10 ** (-1 * (len(str(self.robot.prizing.getLastBid(symbol)).split(".")[1])))
                kwargs = {}

                kwargs["type"] = "MARKET"
                if (side == "buy"):
                    kwargs["units"] = units
                    if (take_proffit != 0):
                        kwargs["takeProfit"] = {
                            "price": str(round(self.robot.prizing.getLastAsk(symbol) + pips * take_proffit, decimales))}
                    if (stop_loss != 0):
                        kwargs["stopLoss"] = {
                            "price": str(round(self.robot.prizing.getLastAsk(symbol) - pips * stop_loss, decimales))}

                if (side == "sell"):
                    kwargs["units"] = -units
                    if (take_proffit != 0):
                        kwargs["takeProfit"] = {
                            "price": str(round(self.robot.prizing.getLastBid(symbol) - pips * take_proffit, decimales))}
                    if (stop_loss != 0):
                        kwargs["stopLoss"] = {
                            "price": str(round(self.robot.prizing.getLastBid(symbol) + pips * stop_loss, decimales))}

                trade=self.robot.api_forex.operate(self, symbol, **kwargs)


                if trade is not None:
                    self.robot.portfolio.add_trade_open(trade)

            except Exception as e:
                self.log.log(e, self.nombreFileException)

        self.robot.symbols_being_trading.remove(symbol)

    def close_trade(self, tradeId, symbol, units=0):

        #to make the symbols we are trading thread standard_deviation_of_returns
        self.robot.symbols_being_trading.append(symbol)
        counter=collections.Counter(self.robot.symbols_being_trading)
        if counter[symbol]==1:
            try:


                kwargs = {}
                kwargs["units"] = units
                self.robot.api_forex.close_trade(self, symbol, tradeId, ** kwargs)
            except Exception as e:
                self.log.log(e, self.nombreFileException)
        self.robot.symbols_being_trading.remove(symbol)


    def close_trades(self, symbol):
        trades_to_delete = []
        if symbol in self.robot.portfolio.trades_open.keys():
            for trade in self.robot.portfolio.trades_open[symbol]:
                    trades_to_delete.append(trade.id)
            for id in trades_to_delete:
                self.close_trade(id, symbol)
