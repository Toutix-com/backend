from flask import Blueprint, jsonify, request
from app.model import Event, Location,db, Ticket, TicketCategory, User

validater_routes = Blueprint('validater', __name__)

@validater_routes.route('/<event_id>/ticket_info', methods=['POST'])
def ticket_validate(event_id):
    data = request.json
    event_id = data.get('eventId')
    ticket_id = data.get('ticketId')
    user_id = data.get('userId')
    category_id = data.get('ticketCategoryId')

    # Validate the ticket
    ticket = Ticket.query.filter_by(TicketID=ticket_id, UserID=user_id, EventID=event_id, CategoryID=category_id).first()
    
    if ticket:
        user_name = User.query.get(user_id).FirstName + ' ' + User.query.get(user_id).LastName
        event = Event.query.get(event_id).Name
        location = Location.query.get(Event.query.get(event_id).LocationID).Name
        ticket_category = TicketCategory.query.get(category_id).Name
        if not ticket.QR_STATUS:
            ticket.QR_STATUS = True
            db.session.commit()
            return jsonify({'message': 'Ticket is valid', 'user_name': user_name, 'event': event, 'location': location, 'ticket_category': ticket_category}), 200
        else:
            return jsonify({'message': 'Ticket has already been validated', 'user_name': user_name, 'event': event, 'location': location, 'ticket_category': ticket_category}), 400
    else:
        return jsonify({'message': 'Ticket not found'}), 404
