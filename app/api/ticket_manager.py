from flask import Flask, Blueprint, request, jsonify
import random
import string
from datetime import datetime
from app.model import User, db, Event, Transaction, Ticket, TicketCategory, StatusEnum
from flask_jwt_extended import create_access_token
from app.api.auth import token_required
from postmarker.core import PostmarkClient
from datetime import datetime
from app.api.storage_utils import *
import base64
import decimal

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

    def send_confirmation(self, event_name, event_DateTime, event_location, ticket_number, user, email, ticket_ids, category):
        
        # Generate QR codes for each ticket
        qr_image_buffers = []
        for ticket_id in ticket_ids:
            qr_image_buffer = generate_qr_code(event_name, ticket_id, user, category.name)
            qr_image_buffers.append(qr_image_buffer)
        
        # Generate PDF with all the QR codes
        pdf_content = generate_ticket_pdf(qr_image_buffers, event_name, user.FirstName, event_location, ticket_number)
        # Convert the PDF content to base64 for attachment
        pdf_content_base64 = base64.b64encode(pdf_content).decode('utf-8')
        pdf_content_buffer = io.BytesIO(pdf_content)
        # Upload the PDF to S3
        file_name = f"{user.Email}_{user.FirstName}"
        s3_response = upload_to_s3(pdf_content_buffer, 'ticketpdfbucket', file_name)
        print(s3_response)
        # Send the OTP to the email address
        send_email = "noreply@toutix.com"
        subject = "Booking confirmation & Ticket for {event_name}"

        # Separate datetime
        datetime_obj = datetime.strptime(str(event_DateTime), '%Y-%m-%d %H:%M:%S')
        date = datetime_obj.date()
        time = datetime_obj.time()
        try:
            postmark = PostmarkClient(server_token=self.SERVER_TOKEN, account_token=self.ACCOUNT_TOKEN)
            email_res = postmark.emails.send_with_template(
                TemplateId=35544926,
                TemplateModel={
                    "Event_Name": event_name,
                    "User": user.FirstName + " " + user.LastName,
                    "Event_Date": date.strftime('%Y-%m-%d'),
                    "Event_Location": f"{event_location['Name']}, {event_location['Address']}",
                    "Event_Time": time.strftime('%H:%M:%S'),
                    "Ticket_number": ticket_number,
                },
                From=send_email,
                To=email,
                Attachments=[{
                "Name": "ticket_confirmation.pdf",
                "Content": pdf_content_base64,
                "ContentType": "application/pdf"
            }]
            )
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
        ticket_ids = [] # List to store the generated ticket IDs
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
            db.session.flush()
            ticket_ids.append(ticket.TicketID)

        db.session.commit()

        # Send confirmation email
        self.send_confirmation(event.Name, event.DateTime, event.location.to_dict(), quantity, user, user.Email, ticket_ids, category)
        print('Confirmation email sent!' + str(user.Email))
        # what do you want to be returned?
        token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

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
        price = decimal.Decimal(price)
        event.resold_tickets += 1
        event.total_resold_revenue += float(price - ticket.initialPrice)  # Total resale revenue is the difference between the price of the ticket and the initial price
        revenu_share = float((price - ticket.initialPrice) * decimal.Decimal('0.4'))
        event.resold_revenue_share_to_business += revenu_share  # Business gets 40% of the resale revenue
        event.total_revenue += revenu_share  # Total revenue is the 40% of the resale revenue + primary ticket sales revenue

        db.session.commit()

        # Delete the existing PDF file in S3
        try:
            delete_response = delete_from_s3(
                bucket='ticketpdfbucket',
                file_name=f"{seller.Email}_{seller.FirstName}"
            )
            print(f"Delete response: {delete_response}")
        except Exception as e:
            # Handle the error here, for example, log the error or print a message
            print(f"Error deleting file from S3: {e}")

        # Generate new QR code with new buyer details
        qr_image_buffer = generate_qr_code(event.Name, ticket_id, user, ticket.ticket_categories.name)
        qr_image_buffers = [qr_image_buffer]

        # Generate PDF with new QR code, and send the PDF to the buyer's email
         # Generate PDF with all the QR codes
        pdf_content = generate_ticket_pdf(qr_image_buffers, event.Name, user.FirstName, event.location, ticket_id)
        # Convert the PDF content to base64 for attachment
        pdf_content_base64 = base64.b64encode(pdf_content).decode('utf-8')
        pdf_content_buffer = io.BytesIO(pdf_content)
        # Upload the PDF to S3
        file_name = f"{user.Email}_{user.FirstName}"
        s3_response = upload_to_s3(pdf_content_buffer, 'ticketpdfbucket', file_name)
        print('S3 response: ',s3_response)
        # Send the OTP to the email address
        send_email = "noreply@toutix.com"
        subject = "Booking confirmation & Ticket for {event.Name}"

        # Separate datetime
        datetime_obj = datetime.strptime(str(event_DateTime), '%Y-%m-%d %H:%M:%S')
        date = datetime_obj.date()
        time = datetime_obj.time()
        try:
            postmark = PostmarkClient(server_token=self.SERVER_TOKEN, account_token=self.ACCOUNT_TOKEN)
            email_res = postmark.emails.send_with_template(
                TemplateId=35544926,
                TemplateModel={
                    "Event_Name": event_name,
                    "User": user.FirstName + " " + user.LastName,
                    "Event_Date": date.strftime('%Y-%m-%d'),
                    "Event_Location": f"{event.location['Name']}, {event.location['Address']}",
                    "Event_Time": time.strftime('%H:%M:%S'),
                    "Ticket_number": ticket_number,
                },
                From=send_email,
                To=email,
                Attachments=[{
                "Name": "ticket_confirmation.pdf",
                "Content": pdf_content_base64,
                "ContentType": "application/pdf"
            }]
            )
            return jsonify({
                "message": f"Confirmation email sent successfully to {email}"
            })
        except Exception as e:
            return jsonify({"message": "Error" + str(e)}), 404
        finally:
            # server.quit()
            pass

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
