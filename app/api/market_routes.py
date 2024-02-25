from flask import Blueprint, jsonify, request
from app.model import MarketplaceListing, Event, db
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

market_routes = Blueprint('markets', __name__)


@market_routes.route('/', methods=['GET'])
def get_markets():
    query = request.args.get('query')
    location = request.args.get('location')
    events = request.args.get('events')

    if query:
        marketplacelistings = MarketplaceListing.query.options(joinedload('events')).filter(
            or_(
                MarketplaceListing.name.ilike(f'%{query}%'),
                Event.location.ilike(f'%{query}%'),
                Event.event_name.ilike(f'%{query}%')
            )
        ).all()
    elif location:
        marketplacelistings = MarketplaceListing.query.options(joinedload('events')).filter(
            Event.location.ilike(f'%{location}%')
        ).all()
    elif events:
        marketplacelistings = MarketplaceListing.query.options(joinedload('events')).filter(
            Event.event_name.ilike(f'%{events}%')
        ).all()
    else:
        marketplacelistings = MarketplaceListing.query.options(joinedload('events')).all()

    return jsonify([marketplacelisting.to_dict() for marketplacelisting in marketplacelistings])


@market_routes.route('/<market_id>', methods=['GET'])
def get_market_by_id(market_id):
    market = Market.query.filter_by(ListingID=market_id).first()

    if market:
        formatted_market = market.to_dict()
        return jsonify({'market':formatted_market})
    else:
        return jsonify({'message': 'Market not found'}), 404
  
