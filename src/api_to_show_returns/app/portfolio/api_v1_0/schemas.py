from marshmallow import fields
from app.ext import ma
class DailyReturnsSchema(ma.Schema):
    symbol = fields.String()
    total_time = fields.Float()
    date = fields.Date()
    amount = fields.Integer()
    profit = fields.Float()
