from flask import Blueprint, jsonify, request
from app.model import Event, Location,db, Ticket, TicketCategory, User

validater_routes = Blueprint('validater', __name__)

@validater_routes.route('/<ticket_id>/ticket_info', methods=['POST'])
def ticket_validate(ticket_id):

    # Validate the ticket
    ticket = Ticket.query.filter_by(TicketID=ticket_id).first()
    
    if ticket:
        user = User.query.get(user_id)
        if user is not None:
            user_name = user.FirstName + ' ' + user.LastName
        else:
            return jsonify({'message': 'User not found'}), 404
        event = Event.query.get(event_id).Name
        location = Location.query.get(Event.query.get(event_id).LocationID).Name
        ticket_category = TicketCategory.query.get(category_id).name
        if not ticket.QR_STATUS:
            ticket.QR_STATUS = True
            db.session.commit()
            return jsonify({'message': 'Ticket is valid','valid': True, 'user_name': user_name, 'event': event, 'location': location, 'ticket_category': ticket_category}), 200
        else:
            return jsonify({'message': 'Ticket has already been validated', 'valid': False, 'user_name': user_name, 'event': event, 'location': location, 'ticket_category': ticket_category}), 400
    else:
        return jsonify({'message': 'Ticket not found'}), 404
