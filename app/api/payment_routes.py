import stripe
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
#from app.config import STRIPE_SECRET_KEY
from app.api.ticket_manager import TicketManager
import os
from app.model import PaymentMethod, User, Event, Ticket, TicketCategory, db, Discount
from app.api.auth import token_required
from decimal import Decimal
from datetime import datetime

payment_routes = Blueprint('payment', __name__)

# Store in .env file
stripe.api_key = os.getenv('STRIPE_API_KEY')
#sk_test_51OjNO1L6oeMlaoGUMj1e7MmK3xoLsj2Gpiaxd1m2xD4KClB6VmfJKxLWtyWuNsjEheUUiKWfN8MlVjyX2UZQ9Ghe00WuZkpqgX

@payment_routes.route('/intent/events/ticket', methods=['POST'])
@token_required
def charge(current_user):

    data = request.json
    user_id = data.get('user_id')
    ticket_category_id = data.get('ticket_category_id')
    event_id = data.get('event_id')
    number_of_tickets = data.get('number_of_tickets')
    coupon_code = data.get('coupon_code')

    if not user_id or not event_id or not ticket_category_id:
        return jsonify({"error": "Event and Ticket details are required."}), 400

    # if user has more than 4 tickets for the same eventid, return error
    user_tickets = Ticket.query.filter_by(UserID=user_id, EventID=event_id).all()
    ticket_category = TicketCategory.query.get(ticket_category_id)
    if len(user_tickets) + number_of_tickets > ticket_category.max_per_person:
        return jsonify({"error": "You have reached the maximum ticket allowed for the same event."}), 400
    
    # Check inventory to see if there are enough tickets
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
        # Apply discount if coupon code is provided
        if coupon_code:
            coupon = Discount.query.filter_by(DiscountID=coupon_code).first()
            current_datetime = datetime.now()
            if not coupon:
                return jsonify({"error": "Invalid coupon code"}), 400
            if coupon.times_used >= coupon.usage_limit:
                return jsonify({"error": "Coupon code has reached its usage limit"}), 400
            if coupon.valid_from > current_datetime:
                return jsonify({"error": "Coupon code is not valid yet"}), 400
            if coupon.valid_until < current_datetime:
                return jsonify({"error": "Coupon code has expired"}), 400
        if coupon.discount_type == 'percentage':
            amount = amount * (1 - coupon.discount_value)
        elif coupon.discount_type == 'fixed':
            amount = amount - coupon.discount_value
        
        coupon.times_used += 1
        db.session.commit()

        # Calculate service fee
        service = amount * 0.1
        total_amount = amount + service

        # Create Payment Intent with metadata containing relevant information
        intent = stripe.PaymentIntent.create(
            amount=int(total_amount*100),
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
@token_required
def marketplace_ticket(current_user):
    data = request.json
    user_id = data.get('user_id')
    ticket_id = data.get('ticket_id')
    resale_price = data.get('resale_price')
    event_id = data.get('event_id')

    if not user_id or not event_id or not ticket_id:
        return jsonify({"error": "Event and Ticket details are required."}), 400

    try:
        # Retrieve user, event, and ticket category information
        user = User.query.get(user_id)
        event = Event.query.get(event_id)
        ticket = Ticket.query.get(ticket_id)
        
        if float(resale_price) <= 2* float(ticket.initialPrice):
            amount = int(float(resale_price) * 100)
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
    endpoint_secret = os.getenv('WEBHOOK_ENDPOINT_SECRET')
    print("payload:", payload)
    print("sig_header:", sig_header)
    print("endpoint_secret:", endpoint_secret)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
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
            print("payment_intent:", payment_intent)
            ticket_manager = TicketManager(payment_intent['metadata']['userID'])
            ticket_manager.purchase_ticket(
                payment_intent['metadata']['eventID'], 
                payment_intent['metadata']['quantity'], 
                payment_intent['id'], 
                payment_intent['metadata']['TransactionAmount'], 
                payment_intent['metadata']['CategoryID'], 
                payment_intent['metadata']['initialPrice']
            )

        elif purchase_type == 'marketplace-tickets':
            # Handles payment and tickets for new buyer of second hand ticket
            ticket_manager = TicketManager(payment_intent['metadata']['userID'])
            ticket_manager.purchase_ticket_marketplace(
                payment_intent['metadata']['sellerID'],
                payment_intent['metadata']['eventID'],
                payment_intent['id'],
                payment_intent['metadata']['price'],
                payment_intent['metadata']['ticketID']
            )

            # Handles refund for seller of second hand ticket
            #Fill the original price
            print(payment_intent['metadata']['ticketID'])
            original_price = Decimal(Ticket.query.get(payment_intent['metadata']['ticketID']).initialPrice)
            resale_price = Decimal(payment_intent['metadata']['price'])

            if resale_price >= original_price:
                refund_amount = int((original_price + Decimal('0.5') * (resale_price - original_price)) * Decimal('100'))
            else:
                refund_amount = int(resale_price * Decimal('100'))
            
            try:
                # Add the credit amount to the seller's account
                seller_id = payment_intent['metadata']['sellerID']
                user = User.query.get(seller_id)
                user.Credit += refund_amount / 100
                print(f"Credit of {refund_amount / 100} added to seller {seller_id}")
                # Commit the changes to the database
                db.session.commit()
                print("Changes committed successfully")
            except Exception as e:
                print(f"Failed to add credit for seller {seller_id}: {e}")


    # Respond to the event
    return '', 200

@payment_routes.route('/coupon', methods=['POST'])
def create_coupon():
    data = request.get_json()

    new_discount = Discount(
        discount_type=data['discount_type'],
        discount_value=data['discount_value'],
        valid_from=datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S'),  # Format example: '2022-12-31 23:59:59'
        valid_until=datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S'),  # Format example: '2023-01-01 00:00:00'
        usage_limit=data.get('usage_limit'),
    )

    db.session.add(new_discount)
    db.session.commit()
    
    return jsonify(new_discount.to_dict()), 201