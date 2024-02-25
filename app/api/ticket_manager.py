from flask import Flask, Blueprint, request, jsonify
import random
import time
import string
from datetime import datetime, timezone
from app.model import User, db, Event, Transaction, Ticket
from flask_jwt_extended import create_access_token
from datetime import timedelta

ticket_routes = Blueprint('ticket', __name__)

class TicketManager:
    def __init__(self, email):
        self.email = email 

    def purchase_ticket(self, event_id, quantity, paymentmethod_id, TransactionAmount, category, seller_id=None, initialprice, price=None):
        user = User.query.filter_by(email=self.email).first()
        if user is None:
            return jsonify({'error': 'User not found'}), 404

        date = datetime.now()
        event = Event.query.get(event_id)

        if event is None:
            return jsonify({'error': 'Event not found'}), 404
        
        # If no seller_id is provided, use a default value
        default_uuid = uuid.UUID('00000000-0000-0000-0000-000000000001')
        if seller_id is None:
            seller_id = default_uuid  # Replace with your default value

        # keep sellerid null for now
        # Remove seat number
        transaction = Transaction(BuyerID=user.id, SellerID=seller_id, PaymentMethodID=paymentmethod_id, TransactionAmount=TransactionAmount, EventID=event_id, TransactionDate=date)
        db.session.add(transaction)
        db.session.flush()

        if price is None:
            price = initialprice

        for _ in range(quantity):
            ticket = Ticket(TransactionID=transaction.TransactionID, UserID=user.id, EventID=event_id, Category=category, Status='Available', Price=price, SeatNumber=seat_number)
            db.session.add(ticket)

        db.session.commit()

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

        ticket.UserID = new_owner.id
        ticket.Status = 'Sold'

        db.session.commit()

        return jsonify({'message': 'Ticket ownership transferred successfully'}), 200