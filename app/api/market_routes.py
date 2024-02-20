from flask import Blueprint, jsonify, request
from app.model import Market, db
from sqlalchemy import or_
from flask_cors import CORS

market_routes = Blueprint('markets', __name__)
CORS(market_routes, resources={r"/*": {"origins": "*"}})

@market_routes.route('/', methods=['GET'])
def get_markets():
  query = request.args.get('query')

  if query:
    markets = Market.query.filter(
      or_(
        Market.Name.ilike(f'%{query}%'),
      )
    ).all()
  else:
    markets = Market.query.all()

  formatted_markets = [market.to_dict() for market in markets]
  return jsonify({'markets':formatted_markets})


@market_routes.route('/<market_id>', methods=['GET'])
def get_market_by_id(market_id):
  market = Market.query.filter_by(MarketID=market_id).first()

  if market:
    formatted_market = market.to_dict()
    return jsonify({'market':formatted_market})
  else:
    return jsonify({'message': 'Market not found'}), 404
  
