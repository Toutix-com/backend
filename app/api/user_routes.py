from flask import Blueprint, jsonify, request
from flask_login import login_required
from datetime import datetime
from app.model import User, Ticket, Event, db, Transaction
from app.api.auth import token_required

user_routes = Blueprint('users', __name__)

@user_routes.route('/')
def get_users():
    users = User.query.all()
    return {'users': [user.to_dict() for user in users]}

@user_routes.route('/<string:id>', methods=['GET'])
@token_required
def get_user_by_id(id):
    user = User.query.get(id)
    return user.to_dict()

@user_routes.route('/<string:id>/tickets', methods=['GET'])
@token_required
def get_user_tickets(id):
    tickets = Ticket.query.filter_by(user_id=id).all()
    return [ticket.to_dict() for ticket in tickets]

@user_routes.route('/<string:user_id>/tickets/<string:ticket_id>', methods=['GET'])
@token_required
def get_ticket_by_ids(user_id, ticket_id):
    ticket = Ticket.query.filter_by(id=ticket_id, user_id=user_id).first()

    if ticket is not None:
        return ticket.to_dict()
    else:
        return jsonify({'error': 'Ticket not found'}), 404

@user_routes.route('/<user_id>/update', methods=['PUT'])
def edit_user(user_id):
    user = User.query.get(UUID(user_id))
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    if 'Address' in data:
        user.Address = data['Address']
    if 'PhoneNumber' in data:
        user.PhoneNumber = data['PhoneNumber']
    if 'FirstName' in data:
        user.FirstName = data['FirstName']
    if 'LastName' in data:
        user.LastName = data['LastName']
    if 'Birthday' in data:
        user.Birthday = datetime.strptime(data['Birthday'], '%Y-%m-%d').date()

    db.session.commit()

    return jsonify({'message': 'User updated successfully'}), 200

@user_routes.route('/<string:user_id>/tickets/<string:ticket_id>', methods=['DELETE'])
@token_required
def delete_ticket(user_id, ticket_id):
    ticket = Ticket.query.filter_by(id=ticket_id, user_id=user_id).first()

    if ticket is None:
        return jsonify({'error': 'Ticket not found'}), 404

    db.session.delete(ticket)
    db.session.commit()

    return jsonify({'message': 'Ticket deleted successfully'})
