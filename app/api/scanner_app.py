from flask import Blueprint, jsonify, request
from app.model import Event, Location,db, Ticket, TicketCategory, User

validater_routes = Blueprint('validater', __name__)

@validater_routes.route('/<ticket_id>/ticket_info', methods=['POST'])
def ticket_validate(ticket_id):

    # Validate the ticket
    ticket = Ticket.query.filter_by(TicketID=ticket_id).first()
    
    if ticket:
        #change how those info are obtained
        user = User.query.get(ticket.UserID)
        user_name = user.FirstName + ' ' + user.LastName
        event = Event.query.get(ticket.EventID).Name
        location = Location.query.get(Event.query.get(ticket.EventID).LocationID).Name
        ticket_category = TicketCategory.query.get(ticket.CategoryID).name
        if not ticket.QR_STATUS or ticket.QR_STATUS == False:
            ticket.QR_STATUS = True
            db.session.commit()
            return jsonify({'message': 'Ticket is valid','valid': True, 'user_name': user_name, 'event': event, 'location': location, 'ticket_category': ticket_category}), 200
        else:
            return jsonify({'message': 'Ticket has already been validated', 'valid': False, 'user_name': user_name, 'event': event, 'location': location, 'ticket_category': ticket_category}), 400
    else:
        return jsonify({'message': 'Ticket not found'}), 404
