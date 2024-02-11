from flask import Blueprint, jsonify, request
from flask_login import login_required
from datetime import datetime
from .models import User, Ticket, Event, db

user_routes = Blueprint('user', __name__)

@user_routes.route('/')
def users():
    users = User.query.all()
    return {'users': [user.to_dict() for user in users]}

@user_routes.route('/<str:id>', methods=['GET'])
@login_required
def user(id):
    user = User.query.get(id)
    return user.to_dict()

@user_routes.route('/<str:id>/tickets', methods=['GET'])
@login_required
def user_tickets(id):
    tickets = Ticket.query.filter_by(user_id=id).all()
    return [ticket.to_dict() for ticket in tickets]

@user_routes.route('/<str:user_id>/tickets/<str:ticket_id>', methods=['GET'])
def get_ticket_by_ids(user_id, ticket_id):
    ticket = Ticket.query.filter_by(id=ticket_id, user_id=user_id).first()

    if ticket is not None:
        return ticket.to_dict()
    else:
        return jsonify({'error': 'Ticket not found'}), 404

@user_routes.route('/<str:user_id>/tickets', methods=['POST'])
@login_required
def create_ticket(user_id):
    data = request.get_json()
    event_id = data.get('event_id')
    quantity = data.get('quantity')
    date = datetime.now()
    event = Event.query.get(event_id)

    if event is not None:
        ticket = Ticket(user_id=user_id, event_id=event_id, quantity=quantity, purchase_date=date)
        db.session.add(ticket)
        db.session.commit()

        return ticket.to_dict()
    else:
        return jsonify({'error': 'Event not found'}), 404

@user_routes.route('/<str:user_id>/tickets/<str:ticket_id>', methods=['DELETE'])
@login_required
def delete_ticket(user_id, ticket_id):
    ticket = Ticket.query.filter_by(id=ticket_id, user_id=user_id).first()

    if ticket is None:
        return jsonify({'error': 'Ticket not found'}), 404

    db.session.delete(ticket)
    db.session.commit()

    return jsonify({'message': 'Ticket deleted successfully'})
