from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.model import User, Ticket, Event, db, TicketCategory
from app.api.auth import token_required
from sqlalchemy import func

organiser_routes = Blueprint('organiser', __name__)

@organiser_routes.route('/<event_id>/ticket_info', methods=['GET'])
def ticket_info( event_id):
    event = Event.query.filter_by(EventID=event_id).first()
    if not event:
        return jsonify({'message': 'Event not found'}), 404
    
    # Retrieve ticket categories for the event
    ticket_categories = TicketCategory.query.filter_by(EventID=event_id).all()

    categories_info = []
    for category in ticket_categories:
        category_info = {
            'CategoryID': str(category.CategoryID),
            'Name': category.name,
            'Price': category.price,
            'Max_Limit': category.max_limit,
            'Tickets_Sold': category.ticket_sold,
            'Tickets_Left': category.max_limit - category.ticket_sold,
            'Max_Per_Person': category.max_per_person,
            'highest_bid': category.price*3,
            'lowest_resold': category.price/2,
            'highest_resold': category.price*2
        }
        categories_info.append(category_info)
    
    total_tickets_sold = event.ticket_sales
    total_tickets = sum(category.max_limit for category in TicketCategory.query.filter_by(EventID=event_id))
    # Attendee List
    attendee_list = Ticket.query.join(User).filter(Ticket.EventID == event_id, Ticket.UserID == User.UserID).add_columns(User.FirstName, User.LastName, User.Email, Ticket.CreationDate, Ticket.QR_STATUS, Ticket.TransactionID, TicketCategory.name).all()
    # Resold tickets
    resold_tickets = event.resold_tickets
    total_resold_revenue = event.total_resold_revenue
    resold_revenu_share_to_business = event.resold_revenue_share_to_business
    total_revenu = event.total_revenue

    print('attendee list', attendee_list)
    print('Attendee List', [{'FirstName': attendee.User.FirstName, 'LastName': attendee.User.LastName, 'Email': attendee.User.Email, 'CreationDate': attendee.CreationDate.isoformat(), 'Status': attendee.Status} for attendee in attendee_list])
    response = {
        'Total_Tickets': total_tickets,
        'Total_Tickets_Sold': total_tickets_sold,
        'Categories': categories_info,
        #'Attendee List': [{'FirstName': attendee.User.FirstName, 'LastName': attendee.User.LastName, 'Email': attendee.User.Email} for attendee in attendee_list],
        'Resold_Tickets': resold_tickets,
        'Total_Resold_Revenue': total_resold_revenue,
        'Resold_Revenue_Share_to_Business': resold_revenu_share_to_business,
        'Total_Revenue': total_revenu

    }

    return jsonify(response), 200





