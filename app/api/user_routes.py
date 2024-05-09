from flask import Blueprint, jsonify, request
from flask_login import login_required
from datetime import datetime
from app.model import User, Ticket, Event, db, Transaction, MarketplaceListing, StatusEnum
from app.api.auth import token_required
from decimal import Decimal

user_routes = Blueprint('users', __name__)

@user_routes.route('/')
def get_users():
    users = User.query.all()
    return {'users': [user.to_dict() for user in users]}

@user_routes.route('/me', methods=['GET'])
@token_required
def get_user_by_id(current_user):
    user = User.query.filter_by(Email=current_user).first()
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return user.to_dict()

@user_routes.route('/me/tickets', methods=['GET'])
@token_required
def get_user_tickets(current_user):
    user_id = User.query.filter_by(Email=current_user).first().UserID
    tickets = Ticket.query.filter_by(UserID=user_id).all()
    return [ticket.to_dict() for ticket in tickets]

@user_routes.route('/me/tickets/<string:ticket_id>', methods=['GET'])
@token_required
def get_ticket_by_ids(current_user, ticket_id):
    user_id = User.query.filter_by(Email=current_user).first().UserID
    ticket = Ticket.query.filter_by(TicketID=ticket_id, UserID=user_id).first()

    if ticket is not None:
        return ticket.to_dict()
    else:
        return jsonify({'error': 'Ticket not found'}), 404
    
@user_routes.route('/me/tickets/<string:ticket_id>/download', methods=['GET'])
@token_required
def download_ticket(current_user, ticket_id):
    ticket = Ticket.query.filter_by(TicketID=ticket_id).first()

    if ticket is None:
        return jsonify({'error': 'Ticket not found'}), 404
    
    if ticket.to_pdf() is None:
        return jsonify({'error': 'Ticket QR code not found'}), 404
    
    return ticket.to_pdf()

@user_routes.route('/me/update', methods=['PUT'])
@token_required
def edit_user(current_user):
    user = User.query.filter_by(Email=current_user).first()
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
    ticket = Ticket.query.filter_by(TicketID=ticket_id, UserID=user_id).first()

    if ticket is None:
        return jsonify({'error': 'Ticket not found'}), 404

    db.session.delete(ticket)
    db.session.commit()

    return jsonify({'message': 'Ticket deleted successfully'})

@user_routes.route('/me/tickets/<string:ticket_id>/list_on_marketplace', methods=['PUT'])
@token_required
def list_ticket_on_marketplace(current_user, ticket_id):
    user_id = User.query.filter_by(Email=current_user).first().UserID
    ticket = Ticket.query.filter_by(TicketID=ticket_id, UserID=user_id).first()
    data = request.get_json()
    price = data.get('price')

    if price > 2*(ticket.initialPrice + Decimal('0.1')*ticket.initialPrice):
        return jsonify({'error': 'Ticket price is too high'}), 400
    ticket.Price = price

    if ticket is None:
        return jsonify({'error': 'Ticket not found'}), 404
    
    if ticket.Status == StatusEnum.ListedonMarketplace:
        return jsonify({'error': 'Ticket is already listed on marketplace'}), 400
    
    if ticket.Status == StatusEnum.Admitted:
        return jsonify({'error': 'Ticket used, can not be listed'}), 400

    ticket.Status = StatusEnum.ListedonMarketplace

    db.session.commit()

    return jsonify({'message': 'Ticket listed on marketplace successfully'}), 200

@user_routes.route('/me/tickets/<string:ticket_id>/delist', methods=['PUT'])
@token_required
def delist_ticket(current_user, ticket_id):
    user_id = User.query.filter_by(Email=current_user).first().UserID
    ticket = Ticket.query.filter_by(TicketID=ticket_id, UserID=user_id).first()

    if ticket is None:
        return jsonify({'error': 'Ticket not found'}), 404
    
    if ticket.Status == StatusEnum.Sold:
        return jsonify({'error': 'Ticket is not listed on marketplace'}), 400
    
    if ticket.Status == StatusEnum.Admitted:
        return jsonify({'error': 'Ticket used, can not be listed'}), 400

    ticket.Status = StatusEnum.Available

    db.session.commit()

    return jsonify({'message': 'Ticket delisted successfully'}), 200