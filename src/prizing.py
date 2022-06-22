from datetime import datetime as datetime
import log
import configparser
config = configparser.ConfigParser()
config.read('../config.properties')

class Prizing:
    def __init__(self, robot):
        self.robot = robot
        self.log = log.log()
        now = datetime.now().strftime("%Y-%m-%d")
        self.nombreFile = "logs/logs_prizing" + now + ".txt"
        self.nombreFileException = "logs/logs_prizingException" + now + ".txt"

    def getLastBid(self, symbol) -> float:
        return self.robot.api_forex.bid_ask(symbol, config.get("Trading", 'bid_symbol'))



    def getLastAsk(self, symbol) -> float:

            return self.robot.api_forex.bid_ask(symbol, config.get("Trading", 'ask_symbol'))

