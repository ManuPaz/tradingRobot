from flask import  Blueprint
from flask_restful import Api, Resource
from .schemas import DailyReturnsSchema
from ..models import DailyReturns
from ...common.error_handling import ObjectNotFound
portfolio_v1_0_bp = Blueprint('portfoliov1_0_bp', __name__)
dailyReturns_schema = DailyReturnsSchema()
api = Api(portfolio_v1_0_bp)
class DailyReturnsListResource(Resource):
    def get(self):
        dailyReturns = DailyReturns.get_all()
        result = dailyReturns_schema.dump(dailyReturns, many=True)
        return result
class DailyReturnsResource(Resource):
    def get(self, symbol):
        dailyReturns = DailyReturns.get_by_symbol(symbol)
        if dailyReturns is None:
            raise ObjectNotFound('El elemento no existe')
        resp = dailyReturns_schema.dump(dailyReturns,many=True)
        return resp
class DailyReturnsResourceByDate(Resource):
    def get(self, date):
        dailyReturns = DailyReturns.get_by_date(date)
        if dailyReturns is None:
            raise ObjectNotFound('El elemento no existe')
        resp = dailyReturns_schema.dump(dailyReturns,many=True)
        return resp
api.add_resource(DailyReturnsListResource, '/api/v1.0/dailyReturns/', endpoint='dailyReturns_list_resource')
api.add_resource(DailyReturnsResource, '/api/v1.0/dailyReturns/symbol/<symbol>/', endpoint='dailyReturns_resource')
api.add_resource(DailyReturnsResourceByDate, '/api/v1.0/dailyReturns/date/<string:date>/', endpoint='dailyReturns_resource_byDate')
