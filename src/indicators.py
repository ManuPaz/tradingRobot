import numpy as np
import operator
import pandas as pd
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import log


class Indicators():
    """
    Represents an Indicator Object which can be used
    to easily add technical indicators to a StockFrame.
    """

    def __init__(self, price_data_frame, robot=None) -> None:
        self.robot = robot
        self.stock_frame = price_data_frame

        self.current_indicators = {}
        self._indicator_signals = {}

        self._indicators_comp_key = []
        self._indicators_key = []
        print("Indicators inited")

    def change(self, column_name: str = 'close') -> pd.DataFrame:
        locals_data = locals()
        del locals_data['self']
        a = column_name + "_change"
        self.current_indicators[a] = {}
        self.current_indicators[a]['args'] = locals_data
        self.current_indicators[a]['func'] = self.change

        self.stock_frame[column_name + "_change"] = self.robot.stock_frame.symbol_groups[column_name].transform(
            lambda x: x.diff()
        )

        return self.stock_frame

    def change_pct(self, column_name: str = 'close') -> pd.DataFrame:
        a = column_name + "_change_pct"
        locals_data = locals()
        del locals_data['self']
        del locals_data['a']

        self.current_indicators[a] = {}
        self.current_indicators[a]['args'] = locals_data
        self.current_indicators[a]['func'] = self.change_pct

        self.stock_frame[column_name + "_change_pct"] = self.robot.stock_frame.symbol_groups[column_name].transform(
            lambda x: x.pct_change()
        )
        self.stock_frame[column_name + "_change_pct"] = self.stock_frame[column_name + "_change_pct"] * 100

        return self.stock_frame

    def sma(self, period: int, column_name: str = 'close') -> pd.DataFrame:
        a = column_name + "_sma"
        locals_data = locals()
        del locals_data['self']
        del locals_data['a']
        self.current_indicators[a] = {}
        self.current_indicators[a]['args'] = locals_data
        self.current_indicators[a]['func'] = self.sma

        self.stock_frame[column_name + "_sma"] = self.robot.stock_frame.symbol_groups[column_name].transform(
            lambda x: x.rolling(window=period).mean()
        )

        return self.stock_frame

    def ema(self, period: int, alpha: float = 0.0, column_name='close') -> pd.DataFrame:
        a = column_name + "_ema"
        locals_data = locals()
        del locals_data['self']
        del locals_data['a']

        self.current_indicators[a] = {}
        self.current_indicators[a]['args'] = locals_data
        self.current_indicators[a]['func'] = self.ema

        self.stock_frame[column_name + "_ema"] = self.robot.stock_frame.symbol_groups[column_name].transform(
            lambda x: x.ewm(span=period).mean()
        )

        return self.stock_frame

    def rsi(self, period: int, method: str = 'wilders', column_name: str = 'close') -> pd.DataFrame:
        a = column_name + "_rsi"
        locals_data = locals()
        del locals_data['self']
        del locals_data['a']
        self.current_indicators[a] = {}
        self.current_indicators[a]['args'] = locals_data
        self.current_indicators[a]['func'] = self.rsi

        self.change(column_name)

        # Define the up days.
        self.stock_frame['up_day'] = self.robot.stock_frame.symbol_groups[column_name + "_change"].transform(
            lambda x: np.where(x >= 0, x, 0)
        )

        # Define the down days.
        self.stock_frame['down_day'] = self.robot.stock_frame.symbol_groups[column_name + "_change"].transform(
            lambda x: np.where(x < 0, abs(x), 0)
        )

        # Calculate the EWMA for the Up days.
        self.stock_frame['ewma_up'] = self.robot.stock_frame.symbol_groups['up_day'].transform(
            lambda x: x.ewm(span=period).mean()
        )

        # Calculate the EWMA for the Down days.
        self.stock_frame['ewma_down'] = self.robot.stock_frame.symbol_groups["down_day"].transform(
            lambda x: x.ewm(span=period).mean()
        )
        """
         # Calculate the EWMA for the Up days.
        self.stock_frame['ewma_up'] = self.robot.stock_frame.symbol_groups['up_day'].transform(
            lambda x : self.ssma(x,period))
        self.stock_frame['ewma_down'] = self.robot.stock_frame.symbol_groups['down_day'].transform(
            lambda x : self.ssma(x,period))"""

        # Calculate the Relative Strength
        relative_strength = self.stock_frame['ewma_up'] / self.stock_frame['ewma_down']

        # Calculate the Relative Strength Index
        relative_strength_index = 100.0 - (100.0 / (1.0 + relative_strength))

        # Add the info to the data frame.
        self.stock_frame[column_name + '_rsi'] = relative_strength_index
        self.stock_frame.drop(
            labels=['up_day','down_day','ewma_up','ewma_down'],
            axis=1,
            inplace=True
        )

        return self.stock_frame

    def standard_deviation(self, period: int, column_name: str = 'close') -> pd.DataFrame:
        a = column_name + "_standar_deviation"
        locals_data = locals()
        del locals_data['self']
        del locals_data['a']
        self.current_indicators[a] = {}
        self.current_indicators[a]['args'] = locals_data
        self.current_indicators[a]['func'] = self.standard_deviation
        # Calculate the Standard Deviation.
        self.stock_frame[column_name + "_standar_deviation"] = self.robot.stock_frame.symbol_groups[
            column_name].transform(
            lambda x: x.ewm(span=period).std()
        )

        return self.stock_frame

    def momentum(self, period: int = 1, column_name: str = 'close') -> pd.DataFrame:
        a = column_name + "_momentum"
        locals_data = locals()
        del locals_data['self']
        del locals_data['a']
        self.current_indicators[a] = {}
        self.current_indicators[a]['args'] = locals_data
        self.current_indicators[a]['func'] = self.momentum

        # Add the Momentum indicator.
        self.stock_frame["aux"] = self.robot.stock_frame.symbol_groups[column_name].transform(lambda x: x.shift(period))
        self.stock_frame[column_name + "_momentum"] = self.stock_frame[column_name] / self.stock_frame["aux"] * 100
        self.stock_frame.drop(
            labels=['aux'],
            axis=1,
            inplace=True
        )

        return self.stock_frame

    def ssma(self, column, period):
        a = []
        for i in range(len(column)):
            if (i < period):
                a.append((column.iloc[0:i + 1]).mean())
            else:
                a.append((a[i - 1] * (period - 1) + column.iloc[i]) / period)
        return a

    def bollinger_bands(self, period: int = 20, column_name: str = 'close') -> pd.DataFrame:
        a = column_name + "_bollinger_bands"
        locals_data = locals()
        del locals_data['self']
        del locals_data['a']
        self.current_indicators[a] = {}
        self.current_indicators[a]['args'] = locals_data
        self.current_indicators[a]['func'] = self.bollinger_bands
        # Define the Moving Avg.
        self.stock_frame[column_name + '_moving_avg'] = self.robot.stock_frame.symbol_groups[column_name].transform(
            lambda x: x.rolling(window=period).mean()
        )

        # Define Moving Std.
        self.stock_frame['moving_std'] = self.robot.stock_frame.symbol_groups[column_name].transform(
            lambda x: x.rolling(window=period).std()
        )

        # Define the Upper Band.
        self.stock_frame[column_name + '_band_upper'] = self.stock_frame[column_name + '_moving_avg'] + 4 * (
            self.stock_frame['moving_std'])

        # Define the lower band
        self.stock_frame[column_name + '_band_lower'] = self.stock_frame[column_name + '_moving_avg'] - 4 * (
            self.stock_frame['moving_std'])

        # Clean up before sending back.
        self.stock_frame.drop(
            labels=['moving_std'],
            axis=1,
            inplace=True
        )

        return self.stock_frame

    def average_true_range(self, period: int = 14, column_name: str = 'close') -> pd.DataFrame:
        a = column_name + "_average_true_range"
        locals_data = locals()
        del locals_data['self']
        del locals_data['a']
        self.current_indicators[a] = {}
        self.current_indicators[a]['args'] = locals_data
        self.current_indicators[a]['func'] = self.average_true_range

        self.stock_frame['aux'] = self.robot.stock_frame.symbol_groups["close"].transform(lambda x: x.shift())
        self.stock_frame['true_range_0'] = abs(self.stock_frame['high'] - self.stock_frame[ 'low'])
        self.stock_frame['true_range_1'] = abs(self.stock_frame[ 'high'] - self.stock_frame["aux"])

        self.stock_frame['true_range_2'] = abs(self.stock_frame[ 'low'] - self.stock_frame["aux"])

        # Grab the Max.
        self.stock_frame['true_range'] = self.stock_frame[['true_range_0', 'true_range_1', 'true_range_2']].max(axis=1)
        self.stock_frame[column_name + '_average_true_range'] = self.robot.stock_frame.symbol_groups[
            'true_range'].transform(
            lambda x: x.ewm(span=period).mean())

        self.stock_frame.drop(
            labels=['true_range_0', 'true_range_1', 'true_range_2', 'true_range', "aux"],
            axis=1,
            inplace=True
        )

        return self.stock_frame

    def dm(self, column_name):
        if column_name <= 0:
            return 0

        else:
            return column_name

    def adx(self, period: int = 14, column_name: str = 'close'):
        a = column_name + "_adx"
        locals_data = locals()
        del locals_data['self']
        del locals_data['a']
        self.current_indicators[a] = {}
        self.current_indicators[a]['args'] = locals_data
        self.current_indicators[a]['func'] = self.adx

        self.average_true_range(column_name=column_name)
        self.stock_frame['aux'] = self.robot.stock_frame.symbol_groups["high"].transform(lambda x: x.shift())
        self.stock_frame['h'] = self.stock_frame[ 'high'] - self.stock_frame["aux"]
        self.stock_frame['aux'] = self.robot.stock_frame.symbol_groups["low"].transform(lambda x: x.shift())
        self.stock_frame['l'] = self.stock_frame["aux"] - self.stock_frame['low']
        self.stock_frame['dm_plus'] = self.stock_frame["h"].transform(
            self.dm)
        self.stock_frame['dm_minus'] = self.stock_frame["l"].transform(
            self.dm)
        self.stock_frame["plus_d"] = self.robot.stock_frame.symbol_groups['dm_plus'].transform(
            lambda x: x.ewm(span=period).mean())
        self.stock_frame["minus_d"] = self.robot.stock_frame.symbol_groups['dm_minus'].transform(
            lambda x: x.ewm(span=period).mean())
        self.stock_frame["plus_d"] = self.stock_frame["plus_d"] / self.stock_frame[column_name + '_average_true_range']
        self.stock_frame["minus_d"] = self.stock_frame["minus_d"] / self.stock_frame[
            column_name + '_average_true_range']

        self.stock_frame['dx'] = abs(self.stock_frame["plus_d"] - self.stock_frame["minus_d"]) / (
                self.stock_frame["plus_d"] + self.stock_frame["minus_d"]) * 100
        self.stock_frame[column_name + "_adx"] = self.robot.stock_frame.symbol_groups['dx'].transform(
            lambda x: x.ewm(span=period).mean())

        return self.stock_frame

    def stochastic_oscillator(self, period: int = 14, column_name: str = 'close') -> pd.DataFrame:
        """Calculates the Stochastic Oscillator.

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the Stochastic Oscillator included.


        """

        locals_data = locals()
        del locals_data['self']
        del locals_data['a']

        self.current_indicators[column_name] = {}
        self.current_indicators[column_name]['args'] = locals_data
        self.current_indicators[column_name]['func'] = self.stochastic_oscillator
        if "symbol" in self.stock_frame.columns:
            print("hola")
        else:
            self.stock_frame.stock_frame['max'] = self.stock_frame.symbol_groups['high'].transform(
                lambda x: x.rolling(window=period).max()
            )
            self.stock_frame.stock_frame['min'] = self.stock_frame.symbol_groups['low'].transform(
                lambda x: x.rolling(window=period).min()
            )

            # Calculate the stochastic_oscillator.
            self.stock_frame.stock_frame['stochastic_oscillator'] = (self.stock_frame.stock_frame['close'] -
                                                                     self.stock_frame.stock_frame['min']) / (
                                                                            self.stock_frame.stock_frame['max'] -
                                                                            self.stock_frame.stock_frame['min'])
            self.stock_frame.stock_frame.drop(
                labels=['max', 'min'],
                axis=1,
                inplace=True
            )

        return self.stock_frame.stock_frame

    def macd(self, fast_period: int = 12, slow_period: int = 26, column_name: str = 'close') -> pd.DataFrame:
        """Calculates the Moving Average Convergence Divergence (MACD).

        Arguments:
        ----
        fast_period {int} -- The number of periods to use when calculating 
            the fast moving MACD. (default: {12})

        slow_period {int} -- The number of periods to use when calculating 
            the slow moving MACD. (default: {26})

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the MACD included.

        """

        locals_data = locals()
        del locals_data['self']

        self.current_indicators[column_name] = {}
        self.current_indicators[column_name]['args'] = locals_data
        self.current_indicators[column_name]['func'] = self.macd

        # Calculate the Fast Moving MACD.
        self.stock_frame.stock_frame['macd_fast'] = self.stock_frame.symbol_groups['close'].transform(
            lambda x: x.ewm(span=fast_period, min_periods=fast_period).mean()
        )

        # Calculate the Slow Moving MACD.
        self.stock_frame.stock_frame['macd_slow'] = self.stock_frame.symbol_groups['close'].transform(
            lambda x: x.ewm(span=slow_period, min_periods=slow_period).mean()
        )

        # Calculate the difference between the fast and the slow.
        self.stock_frame.stock_frame['macd_diff'] = self.stock_frame.stock_frame['macd_fast'] - \
                                                    self.stock_frame.stock_frame['macd_slow']

        # Calculate the Exponential moving average of the fast.
        self.stock_frame.stock_frame['macd'] = self.stock_frame.stock_frame['macd_diff'].transform(
            lambda x: x.ewm(span=9, min_periods=8).mean()
        )

        return self.stock_frame.stock_frame

    def check_signals(self) -> Union[pd.DataFrame, None]:
        """Checks to see if any signals have been generated.

        Returns:
        ----
        {Union[pd.DataFrame, None]} -- If signals are generated then a pandas.DataFrame
            is returned otherwise nothing is returned.
        """

        signals_df = self.robot.stock_frame._check_signals(
            indicators=self._indicator_signals,
            indicators_comp_key=self._indicators_comp_key,
            indicators_key=self._indicators_key
        )

        return signals_df

    def get_indicator_signal(self, indicator: str = None) -> Dict:
        """Return the raw Pandas Dataframe Object.

        Arguments:
        ----
        indicator {Optional[str]} -- The indicator key, for example `ema` or `sma`.

        Returns:
        ----
        {dict} -- Either all of the indicators or the specified indicator.
        """

        if indicator and indicator in self._indicator_signals:
            return self._indicator_signals[indicator]
        else:
            return self._indicator_signals

    def set_indicator_signal(self, indicator: str, buy: float, sell: float, condition_buy: Any, condition_sell: Any,
                             buy_max: float = None, sell_max: float = None, condition_buy_max: Any = None,
                             condition_sell_max: Any = None, symbols: list = None) -> None:
        """Used to set an indicator where one indicator crosses above or below a certain numerical threshold.

        Arguments:
        ----
        indicator {str} -- The indicator key, for example `ema` or `sma`.

        buy {float} -- The buy signal threshold for the indicator.
        
        sell {float} -- The sell signal threshold for the indicator.

        condition_buy {str} -- The operator which is used to evaluate the `buy` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`.
        
        condition_sell {str} -- The operator which is used to evaluate the `sell` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`.

        buy_max {float} -- If the buy threshold has a maximum value that needs to be set, then set the `buy_max` threshold.
            This means if the signal exceeds this amount it WILL NOT PURCHASE THE INSTRUMENT. (defaults to None).
        
        sell_max {float} -- If the sell threshold has a maximum value that needs to be set, then set the `buy_max` threshold.
            This means if the signal exceeds this amount it WILL NOT SELL THE INSTRUMENT. (defaults to None).

        condition_buy_max {str} -- The operator which is used to evaluate the `buy_max` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`. (defaults to None).
        
        condition_sell_max {str} -- The operator which is used to evaluate the `sell_max` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`. (defaults to None).
        symbols {list} -- List of symbols to apply the indicator signal.
        """

        # Add the key if it doesn't exist.
        if indicator not in self._indicator_signals:
            self._indicator_signals[indicator] = {}
            self._indicators_key.append(indicator)
            # Add the signals.
        self._indicator_signals[indicator]['buy'] = buy
        self._indicator_signals[indicator]['sell'] = sell
        self._indicator_signals[indicator]['buy_operator'] = condition_buy
        self._indicator_signals[indicator]['sell_operator'] = condition_sell
        self._indicator_signals[indicator]['symbols'] = symbols

        # Add the max signals
        self._indicator_signals[indicator]['buy_max'] = buy_max
        self._indicator_signals[indicator]['sell_max'] = sell_max
        self._indicator_signals[indicator]['buy_operator_max'] = condition_buy_max
        self._indicator_signals[indicator]['sell_operator_max'] = condition_sell_max

    def set_indicator_signal_compare(self, indicator_1: str, indicator_2: str, condition_buy: Any,
                                     condition_sell: Any, symbols: list) -> None:
        """Used to set an indicator where one indicator is compared to another indicator.

        Overview:
        ----
        Some trading strategies depend on comparing one indicator to another indicator.
        For example, the Simple Moving Average crossing above or below the Exponential
        Moving Average. This will be used to help build those strategies that depend
        on this type of structure.

        Arguments:
        ----
        indicator_1 {str} -- The first indicator key, for example `ema` or `sma`.

        indicator_2 {str} -- The second indicator key, this is the indicator we will compare to. For example,
            is the `sma` greater than the `ema`.

        condition_buy {str} -- The operator which is used to evaluate the `buy` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`.
        
        condition_sell {str} -- The operator which is used to evaluate the `sell` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`.
        symbols {list} -- List of symbols to apply the indicator signal.
        """

        # Define the key.
        key = "{ind_1}_comp_{ind_2}".format(
            ind_1=indicator_1,
            ind_2=indicator_2
        )

        # Add the key if it doesn't exist.
        if key not in self._indicator_signals:
            self._indicator_signals[key] = {}
            self._indicators_comp_key.append(key)
            # Grab the dictionary.
        indicator_dict = self._indicator_signals[key]

        # Add the signals.
        indicator_dict['type'] = 'comparison'
        indicator_dict['indicator_1'] = indicator_1
        indicator_dict['indicator_2'] = indicator_2
        indicator_dict['buy_operator'] = condition_buy
        indicator_dict['sell_operator'] = condition_sell
        indicator_dict['symbols'] = symbols

    def refresh(self):
        """Updates the Indicator columns after adding the new rows."""

        # First update the groups since, we have new rows.
        # Grab all the details of the indicators so far.
        for indicator in self.current_indicators:
            # Grab the function.
            indicator_argument = self.current_indicators[indicator]['args']

            # Grab the arguments.
            indicator_function = self.current_indicators[indicator]['func']

            # Update the function.
            indicator_function(**indicator_argument)
