import v20
from trade import Trade
def get_trades(api: v20.Context, account: str, **kwargs):
    """

       :param api: API to call to operate
       :param account: OANDA account number
       :return: list of trades
       :rtype: list

       kwargs:
        num_trades (optional):
            Number of trades to get from the external API (must be all current day trades) (int)

        symbol (optional):
            Symbol to get trades of (str)

        state:
            "CLOSED" or "OPEN" (str)
       """
    if "num_trades" in kwargs.keys():
        kwargs["count"] = kwargs["num_trades"]
    if "symbol" in kwargs.keys():
        kwargs["instrument"] = kwargs["symbol"]
    kwargs["state"] = kwargs["state"]
    response = api.trade.list(account, **kwargs)
    trades = response.get("trades", 200)
    return trades
def get_trade(api: v20.Context, account: str, trade: str):
    """

           :param api: API to call to operate
           :param account: OANDA account number
           :param trade: trade ID
           :return : list of trades
           :rtype: list
           """
    response = api.trade.get(account, trade)
    try:
        f = response.get('trade', 200)
        return f
    except Exception as e:
        return None
def operate(api: v20.Context, account: str, trade_handler: Trade,symbol:str, **kwargs):
    """

    :param api: API to call to operate
    :param account: OANDA account number
    :param trade_handler:  Trade class instance to log info
    :param symbol: forex pair to operate
    :return : trade information
    :rtype: dict or None

     kwargs:
        type:
            Type of order  (str)
        units:
            number of units to buy or sell

        takeProfit (optional):
            take profit value (float)

        stopLoss (optional):
            stop loss value (float)
    """
    kwargs["instrument"]=symbol
    if "takeProfit" in kwargs.keys():
        kwargs["takeProfitOnFill"]=kwargs["takeProfit"]
    if "stopLoss" in kwargs.keys():
        kwargs["stopLossOnFill"]=kwargs["stopLoss"]
    response = api.order.market(account, **kwargs)
    if response.status == 201:
        cancel = False
        try:
            response.get("orderFillTransaction", 201)
        except Exception:
            cancel = True

        if not cancel:
            if (response.get("orderFillTransaction", 201).tradeOpened != None):
                trade = response.get("orderFillTransaction", 201).tradeOpened
                tradeID = trade.tradeID
                mensaje =  kwargs["instrument"] + ", Trade completed: trade -> " + trade.tradeID + ", tam ->  " + str(
                    trade.units)
                trade_handler.log.log(mensaje, trade_handler.nombreFile)
                response1 = api.trade.get(account, tradeID)
                respuesta = response1.get("trade", 200)
                return respuesta
            if (response.get("orderFillTransaction", 201).tradeReduced != None):
                trade = response.get("orderFillTransaction", 201).tradeReduced
                mensaje =  kwargs["instrument"]+ ", Trade reduced: trade -> " + str(trade.instrument) + ", tam ->  " + str(
                    trade.units)
                trade_handler.log.log(mensaje, trade_handler.nombreFile)
            if (response.get("orderFillTransaction", 201).tradesClosed != None):
                trades = response.get("orderFillTransaction", 201).tradesClosed
                mensaje =  kwargs["instrument"] + ", Trades closed:" + str((len(trades)))
                trade_handler.log.log(mensaje, trade_handler.nombreFile)

        else:
            respuesta = response.get("orderCancelTransaction", 201)
            mensaje =  kwargs["instrument"] + ", " + "Order cancel  en tiempo: " + str(
                respuesta.time) + ", reason: " + respuesta.reason + ", id de la orden: " + str(
                respuesta.orderID) + ", id de la orden de remplazo: " + str(respuesta.replacedByOrderID)
            trade_handler.log.log(mensaje, trade_handler.nombreFile)

    else:
        trade_handler.log.log("Error: " + response.get("errorCode", response.status), trade_handler.nombreFileException)
def close_trade(api: v20.Context, account: str, trade_handler: Trade, symbol: str, tradeId: str, **kwargs):
    """

        :param tradeId: id of trade to close
        :param api: API to call to operate
        :param account: OANDA account number
        :param trade_handler: Trade class instance to log info
        :param symbol: forex pair to operate

         kwargs:

        units:
            number of units to buy or sell

        """
    if kwargs["units"] == 0:
        response = api.trade.close(account, tradeId)
        if response.status == 200:
            trade_handler.log.log("Trade cerrado en simbolo " + str(symbol), trade_handler.nombreFile)
        else:
            trade_handler.log.log("Error al cerrar trade en simbolo  " + str(symbol), trade_handler.nombreFile)
    else:
        response = api.trade.close(account, tradeId, **kwargs)
        if response.status == 200:
            trade_handler.log.log(
                "Trade parcialemente cerrado en simbolo" + str(symbol) + " units: " + str(kwargs["units"]),
                trade_handler.nombreFile)
        else:
            trade_handler.log.log("Error al cerrar trade en simbolo  " + str(symbol), trade_handler.nombreFile)
