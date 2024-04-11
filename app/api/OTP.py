from flask import Flask, Blueprint, request, jsonify
import random
import time
import string
from datetime import datetime, timezone
from app.model import User, db
from flask_jwt_extended import create_access_token
from datetime import timedelta
import smtplib
from postmarker.core import PostmarkClient

otp_routes = Blueprint('otp', __name__)


class OTPManager:
    def __init__(self, email):
        self.email = email
        self.otp = None
        self.expiry = None
        self.SERVER_TOKEN = "da6e6935-98c1-4578-bd01-11e5a76897f3"
        self.ACCOUNT_TOKEN = "a8ae4cbf-763f-4032-ae42-d75dff804fde"

    def generate_store_otp(self, length=6):
        # Generate otp
        digits = string.digits  # String of 0123456789
        self.otp = ''.join(random.choice(digits) for i in range(length))
        self.expiry = int(time.time()) + 300
        # Store OTP
        user = User.query.filter_by(Email=self.email).first()
        if user:
            user.OTP = self.otp
            user.otp_expiry = self.expiry
        else:
            user = User(Email=self.email, OTP=self.otp, otp_expiry=self.expiry)
            db.session.add(user)

        db.session.commit()
        return self.otp, self.expiry

    def send_otp(self):
        # 在这里写发送otp的逻辑
        # Send the OTP to the email address
        # Return json message to frontend
        self.otp, self.expiry = self.generate_store_otp()
        expiry_iso = datetime.fromtimestamp(self.expiry, timezone.utc).isoformat()
        # email = "zhangdaniel0120@gmail.com"
        send_email = "noreplay@toutix.com"

        subject = "Your OTP with Toutix"
        message = f"Your OTP is{self.otp} \n\n The expiry on that is {expiry_iso}"

        text = f"Subject: {subject} \n\n {message}"

        try:

            postmark = PostmarkClient(server_token=self.SERVER_TOKEN, account_token=self.ACCOUNT_TOKEN)
            # template = postmark.templates.get(35527163)
            # postmark.emails.send(
            #     From=send_email,
            #     To=self.email,
            #     Subject=subject,
            #     HtmlBody=message
            # )
            # use template
            postmark.emails.send_with_template(
                TemplateId=35527163,
                TemplateModel={
                    "product_url": "toutix",
                    "product_name": "toutix",
                    "name": "toutix",
                    "action_url": "toutix",
                    "login_url": "toutix",
                    "username": "toutix",
                    "trial_length": "toutix",
                    "trial_start_date": "toutix",
                    "trial_end_date": "toutix",
                    "support_email": "toutix",
                    "live_chat_url": "toutix",
                    "sender_name": "toutix",
                    "help_url": "toutix",
                    "company_name": "toutix",
                    "company_address": "toutix"
                },
                From=send_email,
                To=self.email,
            )
            return jsonify({
                "message": f"OTP sent successfully to {self.email}",
                "otp_expiry": expiry_iso,
                "otp": self.otp
            })
        except Exception as e:
            return jsonify({"message": "Error"}), 404
        finally:
            # server.quit()
            pass

    def generate_access_token(self, identity, expires_delta=timedelta(days=7)):
        access_token = create_access_token(identity=identity, expires_delta=expires_delta)
        return access_token

    def validate_otp(self, input_otp):
        user = User.query.filter_by(Email=self.email).first()

        # Check if the user exists
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Check if the OTP matches and is still valid (not expired)
        current_time = int(time.time())
        if user.OTP == input_otp and current_time < user.otp_expiry:
            access_token = self.generate_access_token(identity=self.email)

            # Store the access token in the user's record
            user.Token = access_token
            db.session.commit()

            return jsonify({
                "message": f"OTP verified successfully for {self.email}",
                "email": self.email,
                "name": user.FirstName,
                "access_token": access_token
            }), 200
        else:
            return jsonify({"error": "Invalid OTP. Please try again."}), 400
