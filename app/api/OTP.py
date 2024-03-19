from flask import Flask, Blueprint, request, jsonify
import random
import time
import string
from datetime import datetime, timezone
from app.model import User, db
from flask_jwt_extended import create_access_token
from datetime import timedelta
import smtplib

otp_routes = Blueprint('otp', __name__)

class OTPManager:
    def __init__(self, email):
        self.email = email
        self.otp = None
        self.expiry = None

    def generate_store_otp(self,length=6):
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
        # Send the OTP to the email address
        # Return json message to frontend
        self.otp, self.expiry = self.generate_store_otp()
        expiry_iso = datetime.fromtimestamp(self.expiry, timezone.utc).isoformat()
        email = "zhangdaniel0120@gmail.com"
        receiver_email = "dxmaptin@gmail.com"

        subject = "Your OTP with Toutix"
        message = f"Your OTP is{self.otp} \n\n The expiry on that is {expiry_iso}"

        text = f"Subject: {subject} \n\n {message}"

        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)  # Using SMTP_SSL for a secure connection
            server.login(email, password)
            server.sendmail(email, receiver_email, text)
        except Exception as e:
            return jsonify({"message": "Error"}), 404
        finally:
            server.quit()
    
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
    