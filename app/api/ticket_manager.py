from flask import Flask, Blueprint, request, jsonify
import random
import string
from datetime import datetime, timezone
from app.model import User, db, Event, Transaction, Ticket, TicketCategory
from flask_jwt_extended import create_access_token
from datetime import timedelta

ticket_routes = Blueprint('ticket', __name__)

@ticket_routes.route('/<ticket_id>/validate', methods=['POST'])
def validate_ticket(ticket_id):
    ticket = Ticket.query.filter_by(TicketID=ticket_id).first()
    if ticket is None:
        return jsonify({'error': 'Ticket not found'}), 404

    if ticket.Status == 'Available':
        ticket.Status = 'Admitted'
        return jsonify({'valid': True}), 200
    else:
        return jsonify({'valid': False}), 200

class TicketManager:
    def __init__(self, user_id):
        self.userID = user_id

    def purchase_ticket(self, event_id, quantity, paymentmethod_id, TransactionAmount, CategoryID, initialprice):
        user = User.query.get(self.userID)
        category = TicketCategory.query.get(CategoryID)
        if user is None:
            return jsonify({'error': 'User not found'}), 404

        date = datetime.now()
        event = Event.query.get(event_id)

        if event is None:
            return jsonify({'error': 'Event not found'}), 404
        
        # Add all the data into the transaction table, and then add the tickets into the ticket table
        # if its a marketplace listing, then there is a sellerID, if not, then there is no sellerID
        
        transaction = Transaction(BuyerID= self.userID, PaymentMethodID=paymentmethod_id, TransactionAmount=TransactionAmount, EventID=event_id, TransactionDate=date)
        db.session.add(transaction)
        db.session.flush()
        
        # Assuming that there is available tickets in the inventory
        for _ in range(int(quantity)):
            if category.ticket_sold >= category.max_limit:
                return {
            'error': 'Not enough tickets available'
            }
            ticket = Ticket(TransactionID=transaction.TransactionID, UserID=self.userID, initialprice=initialprice, EventID=event_id, Category=category.name, Status='Available', Price=initialprice)
            category.ticket_sold += 1
            db.session.add(ticket)

        db.session.commit()

        # what do you want to be returned?
        token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        print(f"Transaction token: {token}")

        return token
    
    def purchase_ticket_marketplace(self, sellerID, event_id, paymentmethod_id, price, ticket_id):
        user = User.query.get(self.userID)
        seller = User.query.get(sellerID)
        ticket = Ticket.query.get(ticket_id)
        
        if user is None or seller is None:
            return jsonify({'error': 'User or seller not found'}), 404
        
        if ticket is None:
            return jsonify({'error': 'Ticket not found'}), 404

        date = datetime.now()
        event = Event.query.get(event_id)

        if event is None:
            return jsonify({'error': 'Event not found'}), 404     
        
        # keep sellerid null for now
        transaction = Transaction(BuyerID= self.userID, SellerID=sellerID, PaymentMethodID=paymentmethod_id, TransactionAmount=price, EventID=event_id, TransactionDate=date)
        db.session.add(transaction)
        db.session.commit()

        # Modify the ticket to have the new owner and status as sold
        ticket.UserID = self.userID
        ticket.Status = 'sold'
        ticket.price = price
        ticket.TransactionID = transaction.TransactionID

        # what do you want to be returned?
        token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        print(f"Transaction token: {token}")

        return token

    def modify_ticket(self, ticket_id, new_owner_email):
        ticket = Ticket.query.get(ticket_id)
        if ticket is None:
            return jsonify({'error': 'Ticket not found'}), 404

        new_owner = User.query.filter_by(email=new_owner_email).first()
        if new_owner is None:
            return jsonify({'error': 'New owner not found'}), 404

        ticket.UserID = new_owner.UserID
        ticket.Status = 'Sold'

        db.session.commit()

        return jsonify({'message': 'Ticket ownership transferred successfully'}), 2001