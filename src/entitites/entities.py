import datetime as dt
class Trade_entity:
    def __init__(self, symbol,trade_aux):
        self.symbol = symbol
        self.initial_units = trade_aux.initialUnits
        self.current_units = trade_aux.currentUnits
        self.unrealized_profit = trade_aux.unrealizedPL
        self.realized_profit = trade_aux.realizedPL
        self.close_price = trade_aux.averageClosePrice
        self.open_price = trade_aux.price
        self.open_time = dt.datetime.fromtimestamp(int(float(trade_aux.openTime)))
        if not trade_aux.closeTime is None:
            self.close_time = dt.datetime.fromtimestamp(int(float(trade_aux.closeTime)))
        else:
            self.close_time=None
        self.state = trade_aux.state
        self.id = trade_aux.id
