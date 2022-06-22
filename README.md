# Forex Trading Robot

This is a robot to trade  forex  using OANDA API. It uses technical indicators and can operate with  15 seconds period or higher using multiple forex symbols. 
<br><br>
With 15 seconds periodicity, it allows  to trade with 20 symbols at the same time, 200 past bars for each symbol and 5 indicators with no problems.<br>
To do that, multithreading is use with trade operations (which do IO operations so free the GIL and we can take advantage of multithreading). <br>
With higher periods suchs as 30 seconds or 1 minutes the number of symbols, bars and indicators can be increased considerably.
<br><br>
The program includes the trading robot, portfolio returns calculation and an API to publish daily returns.
<br><br>
Strategies on multiple symbols using diffferent technical indicators can be configured in a **/assets/trading_config.json**:
```
{
  "trades": {"take_profit":{"EUR_USD": 80,"GBP_USD": 40,
    "EUR_GBP": 40}, "stop_loss":{"EUR_USD": 100,"GBP_USD": 40,
    "EUR_GBP": 40}, "units": {"EUR_USD": 4000,"GBP_USD": 2000,
    "EUR_GBP": 10000}
  },
  "indicators":[{"name":"ema","period":20,"column":"close"},{"name":"rsi","period":14,"column":"close"},
  {"name":"sma","period":100,"column":"close"},{"name":"momentum","period":2,"column":"close"},
  {"name":"adx","period":10,"column":"close","prefix":""}],
  "strategies":[
    {"name":"close_rsi","buy":70,"sell":30,"condition_sell":"menorigual","condition_buy":"mayorigual",
  "symbols": ["EUR_USD","EUR_GBP","EUR_CAD","EUR_AUD","AUD_CAD"]},
    {"name1":"close_ema","name2":"close_sma","buy":0.005,"sell":0.005,"condition_sell":"menorigual","condition_buy":"mayorigual",
  "symbols": ["GBP_USD", "USD_JPY"]}
  ]}
```

Assets (symbols to use) can be configured in  **/assets/assets_config.json**.
<br>
<br>
In OANDA https://www.oanda.com/us-en/trading/ there is the possibility to create a demo account that can be used to test the robot with different strategies.

## Deployment
Database must be created to save daily returns as showed in **assets/createtable.sql**.
Properties file called **config.properties** must be created to load configurations:
```
[configuracionGlobal]
period=S15 (period to trade: S15,S30,M1,M5,M10,M15,M30,H1)
period_portfolio_calculations=M5 (period to calculate portfolio metrics: M1,M5,M10,M15,M30,H1)
accountNumber=<account number of one of your oanda trade accounts>
apikey=<apikey of your OANDA account>
port=443
hostname={api_forex-fxpractice.oanda.com} (api_forex url, can be practice for demo or trade with real money>
ssl=True
datetime_format=UNIX
fechaIni= <date since you want to load your historical trades from OANDA API in YYYY-MM-DD format>
past_bars=200 (number of past bars for each symbol)
[DatabaseSection]
database_host= <host of your database>
database_user= <username  of your database>
database_password= <password of your database>
database_port= <port of your database>
database_name=returns
database_table_name=returnsforex
[API]
secret_key=flask secret key
[Trading]
possibles_portfolio_currencies=EUR USD GBP
currency=EUR
initial_trades_per_symbol_per_date=200
get_previus_returns=False
bid_symbol=B
ask_symbol=A
```

### Requirements

```
pip install -r requirements.txt
```

### Execution🔧

Execute 2 python processes: <br>
	**main_trading.py**, which is the trading robot.<br>
	**main_portfolio_calculation.py**, which calculates portfolio returns and correlations, so you can use then optimize your portfolio.<br>.

```
python main.py
python mainPortfolio.py
```

If you want ro run an API to publish the results, you can do it this way:
```
export FLASK_APP="entrypoint:app"
export FLASK_ENV="development"
export APP_SETTINGS_MODULE="config.default"
```
Run flask in **src/API/**:
```
flask run
```
The API will be in port 5000 by default.
## Features ⚙️
 
* Change symbols,indicators and strategy in **indicators.json** file.
* Find logs in **logs/** folder.
* Daily returns analysis are dumped in json files in **assets/returns** directory.
* Find portfolio information in your database.
* Returns are displayed in the API in the routes **/api_forex/v1.0/dailyReturns**, **/api_forex/v1.0/dailyReturns/symbol/<string:symbol>/** and **/api_forex/v1.0/dailyReturns/date/<string:date>/**.
## Extension 
To keep it simple the robot uses only technical indicators, not relationships between symbols, news and events or techniques such as time series models or machine learning, but it is easy to extend it. You only need to build your time series and add it to the indicators module. For example, you can add an indicator of predictions in real time using a trained model in  prophet and add a rule to trade based on that indicator. 
<br>
Secondly, the robot only uses rules to trade based on one indicator or ><= conditions between two indicators, but this can also be extended easily adding boolean  indicators using logical operations between custom indicators.
## Considerations 
One aspect to think about is why to execute a program with threads and not execute a script each time. The main reason is that if we want to trade using low periods it is usefull to have all the data in memory to increment speed. It would be very slow to load in memory all the past bars that 
we use (by default 200 for each symbol ). If we use higher periods such as 1 hour, it would be possible to execute a script each hour, but my implementation works perfect too for these higher periods.
## Build with 🛠️

* [Python]
* [Flask]
* [Docker]
* [MySQL]



## Autors ✒️
Manuel Paz Pintor



---
⌨️ (https://github.com/ManuPaz) 😊
