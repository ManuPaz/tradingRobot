import configparser
import datetime
import threading
import time

import portfolio
import robot as robot_module
import trade
config = configparser.ConfigParser()
config.read('../config.properties')
time_wait = {"S15":15,"S30":30,"M1": 60, "M5": 60 * 5, "M10": 60 * 10, "M15": 60 * 15, "M30": 60 * 30, "H1": 60 * 60, }
periodicidad = config.get('configuracionGlobal', 'period')
if __name__ == "__main__":
    robot = robot_module.Robot(periodicidad)
    portfolio = portfolio.Portfolio(robot)
    trade = trade.Trade(robot)
    robot.portfolio = portfolio
    robot.trades_module = trade
    while 1:
        tiempo = datetime.datetime.now()

        #init trading robot iteration in other thread
        thread = threading.Thread(target= robot.run)
        thread.start()
        time.sleep(time_wait[periodicidad])


