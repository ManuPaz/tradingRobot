from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class BaseModelMixin:

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def simple_filter(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()
