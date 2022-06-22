import configparser
import pandas as pd
import sqlalchemy
config = configparser.ConfigParser()
config.read('../config.properties')
periodicidad = config.get('configuracionGlobal', 'period')

database_username = config.get('DatabaseSection', 'database_user')
database_password = config.get("DatabaseSection", 'database_password')
database_ip = config.get("DatabaseSection", 'database_host') \
              + ":" + config.get("DatabaseSection", 'database_port')
database_name = config.get("DatabaseSection", 'database_name')
table_name = config.get("DatabaseSection", 'database_table_name')
from pangres import upsert
engine = sqlalchemy.create_engine(
    'mysql+mysqlconnector://{0}:{1}@{2}/{3}'.format(database_username, database_password, database_ip,
                                                    database_name))

dbConnection = engine.connect()
def saveReturns(returns):
    if len(returns) > 0:

        upsert(engine=engine,
               df=returns,
               table_name=table_name,
               if_row_exists='update')

def get_returns():
    sql = "select * from {}".format(table_name)
    stock_frame = pd.read_sql(sql, dbConnection)
    stock_frame.set_index(["symbol","date"], drop=True, inplace=True)
    return stock_frame
