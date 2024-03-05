import stripe
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
#from app.config import STRIPE_SECRET_KEY
from app.api.ticket_manager import TicketManager
import os
from app.model import PaymentMethod, User, Event, Ticket, TicketCategory, db

payment_routes = Blueprint('payment', __name__)

# Store in .env file
stripe.api_key = os.getenv('STRIPE_API_KEY')
#sk_test_51OjNO1L6oeMlaoGUMj1e7MmK3xoLsj2Gpiaxd1m2xD4KClB6VmfJKxLWtyWuNsjEheUUiKWfN8MlVjyX2UZQ9Ghe00WuZkpqgX

@payment_routes.route('/intent/events/ticket', methods=['POST'])
@jwt_required
def charge():

    data = request.json
    user_id = data.get('user_id')
    ticket_category_id = data.get('ticket_category_id')
    event_id = data.get('event_id')
    number_of_tickets = data.get('number_of_tickets')

    if not user_id or not event_id or not ticket_category_id:
        return jsonify({"error": "Event and Ticket details are required."}), 400

    # if user has more than 4 tickets for the same eventid, return error
    user_tickets = Ticket.query.filter_by(UserID=user_id, EventID=event_id).all()
    if len(user_tickets) + number_of_tickets > 4:
        return jsonify({"error": "You can only purchase a maximum of 4 tickets for the same event."}), 400
    
    # Check inventory to see if there are enough tickets
    ticket_category = TicketCategory.query.get(ticket_category_id)
    if ticket_category.ticket_sold + number_of_tickets > ticket_category.max_limit:
        return jsonify({"error": "Not enough tickets available"}), 400
    
    try:
        # Retrieve user, event, and ticket category information
        user = User.query.get(user_id)
        event = Event.query.get(event_id)
        ticket_category = TicketCategory.query.get(ticket_category_id)

        # Calculate the amount based on ticket price and number of tickets
        amount = ticket_category.price * number_of_tickets
        currency = 'gbp'  # Assuming currency is USD

        # Calculate service fee
        service = amount * 0.1
        total_amount = amount + service

        # Create Payment Intent with metadata containing relevant information
        intent = stripe.PaymentIntent.create(
            amount=int(total_amount),
            currency=currency,
            automatic_payment_methods={
                'enabled': True,
            },
            metadata={
                'userID': user.UserID,
                'eventID': event.EventID,
                'purchaseType': 'event-tickets',
                'quantity': number_of_tickets,
                'TransactionAmount': total_amount,
                'CategoryID': ticket_category_id,
                'initialPrice': ticket_category.price
            }
        )

        # Save the Payment Intent ID in the database for future reference
        #payment_method = PaymentMethod(PaymentDetails=intent.id)
        '''db.session.add(payment_method)
        db.session.commit()'''
        return jsonify({"success": True, "paymentIntent": intent.id , 'clientSecret': intent['client_secret']}), 200
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400


@payment_routes.route('/intent/marketplace/ticket', methods=['POST'])
@jwt_required
def marketplace_ticket():
    data = request.json
    user_id = data.get('user_id')
    ticket_id = data.get('ticket_id')
    ticket_category_id = data.get('ticket_category_id')
    resale_price = data.get('resale_price')
    event_id = data.get('event_id')

    if not user_id or not event_id or not ticket_id:
        return jsonify({"error": "Event and Ticket details are required."}), 400

    try:
        # Retrieve user, event, and ticket category information
        user = User.query.get(user_id)
        event = Event.query.get(event_id)
        ticket_category = TicketCategory.query.get(ticket_category_id)
        ticket = Ticket.query.get(ticket_id)
        
        if resale_price <= 2* ticket_category.price:
            amount = resale_price
        else:
            raise ValueError("Resale price cannot be more than double the original price")
        currency = 'gbp'  # Assuming currency is USD

        # Create Payment Intent with metadata containing relevant information
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            automatic_payment_methods={
                'enabled': True,
            },
            metadata={
                'userID': user.UserID,
                'sellerID': ticket.UserID, 
                'userEmail': user.Email,
                'eventID': event.EventID,
                'ticketID': ticket_id,
                'purchaseType': 'marketplace-tickets',
                'price': resale_price
            }
        )

        # Save the Payment Intent ID in the database for future reference
        '''payment_method = PaymentMethod(PaymentDetails=intent.id)
        db.session.add(payment_method)
        db.session.commit()'''
        return jsonify({"success": True, "paymentIntent": intent.id , 'clientSecret': intent['client_secret']}), 200
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400


@payment_routes.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return 'Invalid signature', 400

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        purchase_type = payment_intent['metadata']['purchaseType']

        if purchase_type == 'event-tickets':
            ticket_manager = TicketManager(payment_intent['metadata']['userID'])
            token = ticket_manager.purchase_ticket(
                payment_intent['metadata']['eventID'], 
                payment_intent['metadata']['quantity'], 
                payment_intent['id'], 
                payment_intent['metadata']['TransactionAmount'], 
                payment_intent['metadata']['CategoryID'], 
                payment_intent['metadata']['initialPrice']
            )

        elif purchase_type == 'marketplace-tickets':
            ticket_manager = TicketManager(payment_intent['metadata']['userID'])
            token = ticket_manager.purchase_ticket_marketplace(
                payment_intent['metadata']['sellerID'],
                payment_intent['metadata']['eventID'],
                payment_intent['id'],
                payment_intent['metadata']['price'],
                payment_intent['metadata']['ticketID']
            )
    
    # Respond to the event
    return '', 200

