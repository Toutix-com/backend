from .OTP import OTPManager
from flask import Blueprint, request, jsonify
from ..model import User, db
from flask_login import current_user, login_user, logout_user, login_required

#write blueprint
auth_routes = Blueprint('auth', __name__)

#change the route
@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required."}), 400

    otp_manager = OTPManager(email)
    otp_manager.generate_store_otp()
    if otp_manager.send_otp():
        return jsonify({"message": "OTP sent. Please check your email."}), 200
    else:
        return jsonify({"error": "Failed to send OTP."}), 500

@auth_routes.route('/validateOTP', methods=['POST'])
def validate_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    if not email or not otp:
        return jsonify({"error": "Both email and OTP are required."}), 400

    otp_manager = OTPManager(email)
    if otp_manager.validate_otp(otp):
        user = User.query.filter_by(email= email).first()
        login_user(user)
        return jsonify({"message": "You are logged in."}), 200
    else:
        return jsonify({"error": "Invalid OTP or OTP expired."}), 400

@auth_routes.route('/unauthorized')
def unauthorized():
  """
  Returns unauthorized JSON when flask-login authentication fails
  """
  return {'errors': ['Unauthorized']}, 401


