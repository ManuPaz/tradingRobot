PROPAGATE_EXCEPTIONS = True
import configparser
config = configparser.ConfigParser()
config.read('../../config.properties')
SECRET_KEY= config.get('API', 'secret_key')

database_username = config.get('DatabaseSection', 'database_user')
database_password = config.get("DatabaseSection", 'database_password')
database_ip = config.get("DatabaseSection", 'database_host')\
    +":"+config.get("DatabaseSection", 'database_port')
database_name = config.get("DatabaseSection", 'database_name')
# Database configuration
SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{0}:{1}@{2}/{3}'.format(database_username, database_password,database_ip, database_name)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SHOW_SQLALCHEMY_LOG_MESSAGES = False

ERROR_404_HELP = False
