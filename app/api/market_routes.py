from flask import Blueprint, jsonify, request
from app.model import MarketplaceListing, Event, db, Ticket, User, TicketCategory, StatusEnum
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from app.api.auth import token_required
from decimal import Decimal

market_routes = Blueprint('markets', __name__)


@market_routes.route('/', methods=['GET'])
def get_markets():
    query = request.args.get('query')

    base_query = Ticket.query.filter(Ticket.Status == StatusEnum.ListedonMarketplace).options(joinedload(Ticket.event))

    if query:
        tickets = base_query.filter(
            or_(
                Ticket.event.Name.ilike(f'%{query}%'),
                Ticket.event.location.ilike(f'%{query}%')
            )
        ).all()
    else:
        tickets = base_query.all()

    return jsonify([ticket.to_dict() for ticket in tickets])

    
@market_routes.route('/events', methods=['GET'])
def get_events_with_tickets_on_marketplace():
    tickets = Ticket.query.filter(Ticket.Status == StatusEnum.ListedonMarketplace).all()

    if tickets:
        event_ids = [ticket.EventID for ticket in tickets]
        events = Event.query.filter(Event.EventID.in_(event_ids)).all()

        if events:
            formatted_events = [event.to_dict() for event in events]
            return jsonify({'events': formatted_events})
        else:
            return jsonify({'message': 'No events found for these tickets'}), 404
    else:
        return jsonify({'message': 'No tickets found on the marketplace', "events":[]}), 200

@market_routes.route('/<event_id>', methods=['GET'])
def get_market_by_id(event_id):
    tickets = Ticket.query.filter(Ticket.EventID==event_id, Ticket.Status== StatusEnum.ListedonMarketplace).all()

    if tickets:
        formatted_tickets = [ticket.to_dict() for ticket in tickets]
        return jsonify({'tickets': formatted_tickets})
    else:
        return jsonify({'message': 'No tickets found for this event'}), 404
    
@market_routes.route('/<event_id>/validate', methods=['POST'])
@token_required
def validate_ticket(current_user, event_id):
    # Get the event
    event = Event.query.filter_by(EventID=event_id).first()
    data = request.json
    user_id = data.get('user_id')
    ticket_id = data.get('ticket_id')

    ticket = Ticket.query.filter_by(TicketID=ticket_id).first()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    total_purchased_by_user = Ticket.query.filter_by(UserID=user_id, EventID=event_id).count()
    # Modify to use a variable later
    is_eligible_to_purchase = True
    if total_purchased_by_user + 1 > 4:
        is_eligible_to_purchase = False

    price = ticket.Price
    print(type(price))
    service = price * Decimal('0.1')
    total = price + service

    return jsonify({
        'is_eligible_to_purchase': is_eligible_to_purchase,
        'total': total,
        'service': service,
    }), 200
  
