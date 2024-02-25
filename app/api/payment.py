import stripe
from flask import Blueprint, request, jsonify
from app.model import PaymentMethod, User, Event, Ticket, TicketCategory, db
from flask_jwt_extended import jwt_required
from app.config import STRIPE_SECRET_KEY

payment_routes = Blueprint('payment', __name__)

# Store in .env file
stripe.api_key = sk_test_51OjNO1L6oeMlaoGUMj1e7MmK3xoLsj2Gpiaxd1m2xD4KClB6VmfJKxLWtyWuNsjEheUUiKWfN8MlVjyX2UZQ9Ghe00WuZkpqgX

@payment_routes.route('/intent/events/ticket', methods=['POST'])
@jwt_required
def charge():
    data = request.json
    user_id = data.get('userID')
    ticket_category_id = data.get('ticketCategoryID')
    event_id = data.get('eventID')
    number_of_tickets = data.get('numberOfTickets')

    if not user_id or not event_id or not ticket_category_id:
        return jsonify({"error": "Event and Ticket details are required."}), 400

    try:
        # Retrieve user, event, and ticket category information
        user = User.query.get(user_id)
        event = Event.query.get(event_id)
        ticket_category = TicketCategory.query.get(ticket_category_id)

        # Calculate the amount based on ticket price and number of tickets
        amount = ticket_category.price * number_of_tickets
        currency = 'usd'  # Assuming currency is USD

        # Calculate service fee
        service = amount * 0.1
        total_amount = amount + service

        # Create Payment Intent with metadata containing relevant information
        intent = stripe.PaymentIntent.create(
            amount=total_amount,
            currency=currency,
            automatic_payment_methods={
                'enabled': True,
            },
            metadata={
                'userID': user.id,
                'eventID': event.id,
                'ticketCategoryID': ticket_category.id,
                'ticketCategoryName': ticket_category.name,
                'numberOfTickets': number_of_tickets,
                'purchaseType': 'event-tickets',
                'quantity': number_of_tickets,
                'transactionAmount': total_amount,
                'category': ticket_category.name,
                'initialPrice': ticket_category.price
            }
        )

        # Save the Payment Intent ID in the database for future reference
        payment_method = PaymentMethod(PaymentDetails=intent.id)
        db.session.add(payment_method)
        db.session.commit()
        return jsonify({"success": True, "paymentIntent": intent.id , 'clientSecret': intent['client_secret']}), 200
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400


@payment_routes.route('/intent/marketplace/ticket', methods=['POST'])
@jwt_required
def charge():
    data = request.json
    user_id = data.get('userID')
    ticket_id = data.get('ticketID')
    ticket_category_id = data.get('ticketCategoryID')
    resale_price = data.get('resalePrice')
    event_id = data.get('eventID')

    if not user_id or not event_id or not ticket_id:
        return jsonify({"error": "Event and Ticket details are required."}), 400

    try:
        # Retrieve user, event, and ticket category information
        user = User.query.get(user_id)
        event = Event.query.get(event_id)
        ticket_category = TicketCategory.query.get(ticket_category_id)
        ticket = Ticket.query.get(ticket_id)

        # Calculate the amount based on ticket price and number of tickets
        amount = ticket_category.price * number_of_tickets
        currency = 'usd'  # Assuming currency is USD

        # Create Payment Intent with metadata containing relevant information
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            automatic_payment_methods={
                'enabled': True,
            },
            metadata={
                'userID': user.id,
                'userEmail': user.email,
                'eventID': event.id,
                'eventName': event.name,
                'ticketID': ticket_id,
                'purchaseType': 'marketplace-tickets'

                # Add any other relevant information here
            }
        )

        # Save the Payment Intent ID in the database for future reference
        payment_method = PaymentMethod(PaymentDetails=intent.id)
        db.session.add(payment_method)
        db.session.commit()
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
        # Update database based on payment status
        # For example, update ticket purchase status to 'paid'
        
    
    # Respond to the event
    return '', 200

