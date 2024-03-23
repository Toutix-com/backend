from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.model import User, Ticket, Event, db, TicketCategory
from app.api.auth import token_required
from sqlalchemy import func

organiser_routes = Blueprint('organiser', __name__)

@organiser_routes.route('/<event_id>/ticket_info', methods=['GET'])
def ticket_info(event_id):
    
    event = Event.query.filter_by(EventID=event_id).first()
    if not event:
        return jsonify({'message': 'Event not found'}), 404
    
    total_tickets_sold = sum(category.ticket_sold for category in TicketCategory.query.filter_by(EventID=event_id))
    total_tickets = sum(category.max_limit for category in TicketCategory.query.filter_by(EventID=event_id))
    # Attendee List
    attendee_list = Ticket.query.join(User).filter(Ticket.EventID == event_id, Ticket.UserID == User.UserID).add_columns(User.FirstName, User.LastName, User.Email, Ticket.CreationDate, Ticket.Status, Ticket.TransactionID).all()
    # Ticket Types and Sales Status
    ticket_types = TicketCategory.query.with_entities(TicketCategory.name, func.sum(TicketCategory.max_limit - TicketCategory.ticket_sold)).filter_by(EventID=event_id).group_by(TicketCategory.name).all()

    response = {
        'Total Tickets': total_tickets,
        'Total Tickets Sold': total_tickets_sold,
        'Ticket Types': [{'Category': type_.name, 'Count': count} for type_, count in ticket_types],
        'Attendee List': [{'FirstName': attendee.User.FirstName, 'LastName': attendee.User.LastName, 'Email': attendee.User.Email, 'CreationDate': attendee.CreationDate.isoformat(), 'Status': attendee.Status, 'TransactionID': str(attendee.TransactionID)} for attendee in attendee_list]
    }

    return jsonify(response), 200



