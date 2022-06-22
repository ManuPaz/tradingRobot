import configparser
import datetime
import datetime as dt
import threading
import time

import portfolio
import robot as robot_module
config = configparser.ConfigParser()
config.read('../config.properties')
time_wait = {"M1": 60, "M5": 60 * 5, "M10": 60 * 10, "M15": 60 * 15, "M30": 60 * 30, "H1": 60 * 60, }
periodicidad = config.get('configuracionGlobal', 'period_portfolio_calculations')
get_previus_returns=True if config.get('configuracionGlobal', 'period_portfolio_calculations')=="True" else False
if __name__ == "__main__":
    robot = robot_module.Robot(periodicidad)
    portfolio = portfolio.Portfolio(robot)
    robot.portfolio = portfolio
    if get_previus_returns:
        portfolio.set_positions()
        portfolio.initial_save_returns()
    while 1:
        tiempo = datetime.datetime.now()
        thread = threading.Thread(target=robot.portfolio_operations)
        thread.start()
        time.sleep(time_wait[periodicidad])

