from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.model import User, Ticket, Event, db, TicketCategory
from app.api.auth import token_required
from sqlalchemy import func
import csv
from io import BytesIO, StringIO
from flask import make_response, send_file

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
    attendee_list = Ticket.query.join(User).join(TicketCategory).filter(Ticket.EventID == event_id, Ticket.UserID == User.UserID).add_columns(User.FirstName, User.LastName, User.Email, Ticket.CreationDate, Ticket.QR_STATUS, Ticket.TransactionID, TicketCategory.name).all()
    
    # Resold tickets
    resold_tickets = event.resold_tickets
    total_resold_revenue = event.total_resold_revenue
    resold_revenu_share_to_business = event.resold_revenue_share_to_business
    total_revenu = event.total_revenue

    response = {
        'Total_Tickets': total_tickets,
        'Total_Tickets_Sold': total_tickets_sold,
        'Categories': categories_info,
        'Attendee List':  [
    {
        'TicketID': str(item[0]),
        'FirstName': item[1],
        'LastName': item[2],
        'Email': item[3],
        'CreationDate': item[4].isoformat(),
        'Status': 'Used' if item[5] else 'Not Used',
        'TransactionID': str(item[6]),
        'TicketCategory': item[7]
    }
    for item in attendee_list
],
        'Resold_Tickets': resold_tickets,
        'Total_Resold_Revenue': total_resold_revenue,
        'Resold_Revenue_Share_to_Business': resold_revenu_share_to_business,
        'Total_Revenue': total_revenu

    }

    return jsonify(response), 200

@organiser_routes.route('/<event_id>/download_csv', methods=['GET'])
def download_csv(event_id):
    # Attendee List
    attendee_list = Ticket.query.join(User).join(TicketCategory).filter(
        Ticket.EventID == event_id, Ticket.UserID == User.UserID).add_columns(
        User.FirstName, User.LastName, User.Email, Ticket.CreationDate, Ticket.QR_STATUS,
        Ticket.TransactionID, TicketCategory.name).all()

    # Generate CSV
    csv_file = StringIO()
    writer = csv.writer(csv_file)

    # Write the header row
    writer.writerow(['FirstName', 'LastName', 'Email', 'CreationDate', 'QR_STATUS', 'TransactionID', 'TicketCategoryName', 'Admitted'])

    # Write each attendee as a row
    for attendee in attendee_list:
        writer.writerow([
            attendee.FirstName,
            attendee.LastName,
            attendee.Email,
            attendee.CreationDate.isoformat(),
            attendee.QR_STATUS,
            attendee.TransactionID,
            attendee.name,
            'Yes' if attendee.QR_STATUS == 'Admitted' else 'No'
        ])

    # Reset the file pointer to the beginning
    csv_file.seek(0)

    # Convert StringIO to BytesIO for send_file
    bytes_file = BytesIO()
    bytes_file.write(csv_file.getvalue().encode('utf-8'))
    bytes_file.seek(0)

    return send_file(
        bytes_file,
        as_attachment=True,
        download_name='attendee_list.csv',
        mimetype='text/csv'
    )
