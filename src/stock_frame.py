import datetime as dt
import pandas as pd
import configparser
config = configparser.ConfigParser()
config.read('../config.properties')
class StockFrame:
    def __init__(self, robot, past_bars):
        self.stock_frame = pd.DataFrame(columns=['symbol', 'time', 'open', 'close', 'high', 'low', 'volume'])

        self.robot = robot
        self.past_bars = past_bars
        self.symbols = []
        self._symbol_groups = None
        self._symbol_rolling_groups = None
        self.k = 0
        print("Stock frame inited")

    @property
    def symbol_groups(self):
        """Returns the Groups in the StockFrame.

        Overview:
        ----
        Often we will want to apply operations to a each symbol. The
        `symbols_groups` property will return the dataframe grouped by
        each symbol.

        Returns:
        ----
        {DataFrameGroupBy} -- A `pandas.core.groupby.GroupBy` object with each symbol.
        """

        # Group by Symbol.
        self._symbol_groups = self.stock_frame.groupby(
            by='symbol',
            as_index=False,
            sort=True
        )

        return self._symbol_groups

    def symbol_rolling_groups(self, size: int):
        """Grabs the windows for each group.

        Arguments:
        ----
        size {int} -- The size of the window.

        Returns:
        ----
        {RollingGroupby} -- A `pandas.core.window.RollingGroupby` object.
        """

        # If we don't a symbols group, then create it.
        if not self._symbol_groups:
            self.symbol_groups

        self._symbol_rolling_groups = self._symbol_groups.rolling(
            size)

        return self._symbol_rolling_groups

    def addSymbol(self, symbol, periodicidad):
        e = self.stock_frame.iloc[:, 0]

        esta = False
        for i in e:
            if i == symbol:
                esta = True
                break
        if esta == False:
            self.symbols.append(symbol)
            kwargs = {}
            kwargs["period"] = periodicidad
            kwargs["num_bars"] = self.past_bars
            kwargs["price"] = config.get("Trading", 'bid_symbol')
            self.robot.api_forex.get_data(self.stock_frame, symbol, **kwargs)


    def addRow(self, symbol, periodicidad):
        this_symbol = self.stock_frame.loc[:, 'symbol'] == symbol

        dataframe_symbol = self.stock_frame.loc[this_symbol]

        kwargs = {}
        kwargs["period"] = periodicidad
        tiempo = dataframe_symbol.loc[dataframe_symbol.index[-1],"time"]
        kwargs["price"] =  config.get("Trading", 'bid_symbol')
        kwargs["from_time"] = dt.datetime.timestamp(tiempo)
        self.robot.api_forex.get_last_rows(self.stock_frame, symbol, tiempo, dataframe_symbol, **kwargs)




    def _check_signals(self, indicators: dict, indicators_comp_key, indicators_key):
        """Returns the last row of the StockFrame if conditions are met.

        Overview:
        ----
        Before a trade is executed, we must check to make sure if the
        conditions that warrant a `buy` or `sell` signal are met. This
        method will take last row for each symbol in the StockFrame and
        compare the indicator column values with the conditions specified
        by the user.

        If the conditions are met the row will be returned back to the user.

        Arguments:
        ----
        indicators {dict} -- A dictionary containing all the indicators to be checked
            along with their buy and sell criteria.

        indicators_comp_key List[str] -- A list of the indicators where we are comparing
            one indicator to another indicator.

        indicators_key List[str] -- A list of the indicators where we are comparing
            one indicator to a numerical value.

        Returns:
        ----
        {Union[pd.DataFrame, None]} -- If signals are generated then, a pandas.DataFrame object
            will be returned. If no signals are found then nothing will be returned.
        """

        # Grab the last rows.
        stock_frame_aux = self.stock_frame.set_index(keys=['symbol', 'time'])
        last_rows = stock_frame_aux.groupby(
            by='symbol',
            as_index=False,
            sort=True
        ).tail(1)

        # Define a list of conditions.
        conditions = []

        # Check to see if all the columns exist.
        if self.do_indicator_exist(column_names=indicators_key):
            for indicator in indicators_key:
                column = last_rows[indicator]

                buy_condition_target = indicators[indicator]['buy']
                sell_condition_target = indicators[indicator]['sell']

                buy_condition_operator = indicators[indicator]['buy_operator']
                sell_condition_operator = indicators[indicator]['sell_operator']

                condition_1: pd.Series = buy_condition_operator(
                    column, buy_condition_target
                )
                condition_2: pd.Series = sell_condition_operator(
                    column, sell_condition_target
                )
                condition_1 = condition_1.loc[
                    condition_1.index.get_level_values(0).isin(indicators[indicator]['symbols'])].where(
                    lambda x: x == True).dropna()
                condition_2 = condition_2.loc[
                    condition_2.index.get_level_values(0).isin(indicators[indicator]['symbols'])].where(
                    lambda x: x == True).dropna()

                conditions.append(('buys', condition_1))
                conditions.append(('sells', condition_2))

        check_indicators = []

        for indicator in indicators_comp_key:
            parts = indicator.split('_comp_')
            check_indicators += parts

        if self.do_indicator_exist(column_names=check_indicators):
            for indicator in indicators_comp_key:
                # Split the indicators.
                parts = indicator.split('_comp_')

                # Grab the indicators that need to be compared.
                indicator_1 = last_rows[parts[0]]
                indicator_2 = last_rows[parts[1]]

                if indicators[indicator]['buy_operator']:
                    buy_condition_operator = indicators[indicator]['buy_operator']

                    condition_1: pd.Series = buy_condition_operator(
                        indicator_1, indicator_2
                    )

                    condition_1 = condition_1.loc[
                        condition_1.index.get_level_values(0).isin(indicators[indicator]['symbols'])].where(
                        lambda x: x == True).dropna()
                    conditions.append(('buys', condition_1))

                if indicators[indicator]['sell_operator']:
                    sell_condition_operator = indicators[indicator]['sell_operator']

                    condition_2: pd.Series = sell_condition_operator(
                        indicator_1, indicator_2
                    )

                    condition_2 = condition_2.loc[
                        condition_2.index.get_level_values(0).isin(indicators[indicator]['symbols'])].where(
                        lambda x: x == True).dropna()
                    conditions.append(('sells', condition_2))

        return conditions

    def do_indicator_exist(self, column_names) -> bool:
        """Checks to see if the indicator columns specified exist.

        Overview:
        ----
        The user can add multiple indicator columns to their StockFrame object
        and in some cases we will need to modify those columns before making trades.
        In those situations, this method, will help us check if those columns exist
        before proceeding on in the code.

        Arguments:
        ----
        column_names {List[str]} -- A list of column names that will be checked.

        Raises:
        ----
        KeyError: If a column is not found in the StockFrame, a KeyError will be raised.

        Returns:
        ----
        bool -- `True` if all the columns exist.
        """

        if set(column_names).issubset(self.stock_frame.columns):
            return True
        else:
            raise KeyError("The following indicator columns are missing from the StockFrame: {missing_columns}".format(
                missing_columns=set(column_names).difference(
                    self.stock_frame.columns)
            ))
