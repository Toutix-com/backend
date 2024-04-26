from flask import Flask, Blueprint, request, jsonify
import random
import string
from datetime import datetime, timezone
from app.model import User, db, Event, Transaction, Ticket, TicketCategory, StatusEnum
from flask_jwt_extended import create_access_token
from datetime import timedelta
from app.api.auth import token_required
from postmarker.core import PostmarkClient
from datetime import datetime

ticket_routes = Blueprint('ticket', __name__)


@ticket_routes.route('/<ticket_id>/validate', methods=['POST'])
@token_required
def validate_ticket(current_user, ticket_id):
    ticket = Ticket.query.filter_by(TicketID=ticket_id).first()
    if ticket is None:
        return jsonify({'error': 'Ticket not found'}), 404

    if ticket.Status == StatusEnum.Available:
        ticket.Status = StatusEnum.Admitted
        db.session.commit()
        return jsonify({'Success': True}), 200
    else:
        return jsonify({'Success': False}), 200


@ticket_routes.route('/<ticket_id>', methods=['GET'])
@token_required
def get_ticket_by_ids(current_user, ticket_id):
    ticket = Ticket.query.filter_by(TicketID=ticket_id).first()

    if ticket is not None:
        return ticket.to_dict()
    else:
        return jsonify({'error': 'Ticket not found'}), 404


class TicketManager:
    def __init__(self, user_id):
        self.userID = user_id
        self.SERVER_TOKEN = "da6e6935-98c1-4578-bd01-11e5a76897f3"
        self.ACCOUNT_TOKEN = "a8ae4cbf-763f-4032-ae42-d75dff804fde"

    def send_confirmation(self, event_name, event_DateTime, event_location, ticket_number, user, email):
        SERVER_TOKEN = "da6e6935-98c1-4578-bd01-11e5a76897f3"
        ACCOUNT_TOKEN = "a8ae4cbf-763f-4032-ae42-d75dff804fde"
        # Send the OTP to the email address
        # Return json message to frontend
        send_email = "noreply@toutix.com"

        subject = "Booking confirmation & Ticket for {event_name}"

        print('Date: ', event_DateTime)
        # Separate datetime
        datetime_obj = datetime.strptime(str(event_DateTime), '%Y-%m-%d %H:%M:%S')
        date = datetime_obj.date()
        time = datetime_obj.time()
        print(date, time)
        try:
            postmark = PostmarkClient(server_token=self.SERVER_TOKEN, account_token=self.ACCOUNT_TOKEN)
            email_res = postmark.emails.send_with_template(
                TemplateId=35544926,
                TemplateModel={
                    "Event_Name": event_name,
                    "User": user.FirstName,
                    "Event_Date": date,
                    "Event_Location": event_location,
                    "Event_Time": time,
                    "Ticket_number": ticket_number,
                },
                From=send_email,
                To=email,
            )
            print(email_res)
            return jsonify({
                "message": f"Confirmation email sent successfully to {email}"
            })
        except Exception as e:
            return jsonify({"message": "Error" + str(e)}), 404
        finally:
            # server.quit()
            pass

    def purchase_ticket(self, event_id, quantity, paymentmethod_id, TransactionAmount, CategoryID, initialPrice):
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

        transaction = Transaction(BuyerID=self.userID, PaymentMethodID=paymentmethod_id,
                                  TransactionAmount=TransactionAmount, EventID=event_id, TransactionDate=date)
        db.session.add(transaction)
        db.session.flush()

        # Assuming that there is available tickets in the inventory
        for _ in range(int(quantity)):
            if category.ticket_sold >= category.max_limit:
                return {
                    'error': 'Not enough tickets available'
                }
            ticket = Ticket(TransactionID=transaction.TransactionID, UserID=self.userID, EventID=event_id,
                            CategoryID=CategoryID, Status=StatusEnum.Available, initialPrice=initialPrice)
            # Ticket sales tracking
            category.ticket_sold += 1
            event.ticket_sales += 1  # everytime a ticket is bought, the total count is added
            event.total_revenue += int(float(initialPrice))  # everytime a ticket is bought, the initial price is added
            db.session.add(ticket)

        print('Commit to DB')
        db.session.commit()

        # Send confirmation email
        print('Sending confirmation email...' + str(user.Email))
        self.send_confirmation(event.Name, event.DateTime, event.location, quantity, user, user.Email)
        print('Confirmation email sent!' + str(user.Email))
        # what do you want to be returned?
        token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        print(f"Transaction token: {token}")

        return token

    # def generate_qr_code(ticket_id, event_name, attendee_name):
    #     qr = qrcode.QRCode(
    #         version=1,
    #         error_correction=qrcode.constants.ERROR_CORRECT_L,
    #         box_size=10,
    #         border=4,
    #     )
    #     qr_data = f"Ticket ID: {ticket_id}\nEvent: {event_name}\nAttendee: {attendee_name}"
    #     qr.add_data(qr_data)
    #     qr.make(fit=True)
    #
    #     qr_img = qr.make_image(fill_color="black", back_color="white")
    #     qr_img.save(f"ticket_{ticket_id}_qr.png")
    #     return qr_img

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
        transaction = Transaction(BuyerID=self.userID, SellerID=sellerID, PaymentMethodID=paymentmethod_id,
                                  TransactionAmount=price, EventID=event_id, TransactionDate=date)
        db.session.add(transaction)
        db.session.commit()

        # Modify the ticket to have the new owner and status as sold
        ticket.UserID = self.userID
        ticket.Status = StatusEnum.Sold
        ticket.price = price
        ticket.TransactionID = transaction.TransactionID

        # Ticket sales tracking
        event.resold_tickets += 1
        event.total_resold_revenue += price - ticket.initialPrice  # Total resale revenue is the difference between the price of the ticket and the initial price
        revenu_share = (price - ticket.initialPrice) * 0.4
        event.resold_revenue_share_to_business += revenu_share  # Business gets 40% of the resale revenue
        event.total_revenue += revenu_share  # Total revenue is the 40% of the resale revenue + primary ticket sales revenue

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

        ticket.UserID = new_owner.UserID
        ticket.Status = StatusEnum.Sold

        db.session.commit()

        return jsonify({'message': 'Ticket ownership transferred successfully'}), 2001
