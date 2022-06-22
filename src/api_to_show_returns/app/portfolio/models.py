import configparser
import sqlalchemy as sa
from app.db import db, BaseModelMixin
config = configparser.ConfigParser()
config.read('../../config.properties')
tableName = config.get("DatabaseSection", 'database_table_name')
from sqlalchemy import Table, MetaData
metadata = MetaData()


class DailyReturns(db.Model, BaseModelMixin):
    __table__ = db.Model.metadata.tables[tableName]
    @classmethod
    def get_by_symbol(cls, symbol):
        results = cls.query.filter_by(symbol=symbol).all()

        return results

    @classmethod
    def get_by_date(cls, date):
        results = cls.query.filter_by(date=date).all()

        return results
