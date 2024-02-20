from .OTP import OTPManager
from flask import Blueprint, request, jsonify
from app.model import User, db
from flask_login import current_user, login_user, logout_user, login_required
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import time
from flask_cors import CORS

#write blueprint
auth_routes = Blueprint('auth', __name__)

CORS(auth_routes, resources={r"/*": {"origins": "*"}})

def token_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({'message': 'Invalid access token'}), 401
        return f(current_user, *args, **kwargs)
    return decorated_function

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
        return otp_manager.send_otp(), 200
    else:
        return jsonify({"error": "Failed to send OTP."}), 400

@auth_routes.route('/validateOTP', methods=['POST'])
def validate_otp():
    data = request.json
    email = data.get('email')
    otp = data.get('otp')
    if not email or not otp:
        return jsonify({"error": "Both email and OTP are required."}), 400
    
    user = User.query.filter_by(Email=email).first()
    if otp != user.OTP or int(time.time()) > user.otp_expiry:
        return jsonify({"error": "Invalid OTP or OTP expired."}), 400
    
    otp_manager = OTPManager(email)
    if not otp_manager.validate_otp(otp):
        return jsonify({"error": "Invalid OTP or OTP expired."}), 400

    if not user:
        return jsonify({"error": "Invalid User."}), 400

    # Update last login time to current datetime
    user.last_login = datetime.utcnow()

    # Determine if it's the user's first login
    first_time_login = user.last_login is None

    # Get access token
    access_token = user.Token

    # Update last_login in the database
    db.session.commit()

    login_user(user, force=True)

    # Return access token, email, and first_time_login boolean
    return jsonify({
        "access_token": access_token,
        "email": user.Email,
        "first_time_login": first_time_login,
        "message": "You are logged in."
    }), 200

@auth_routes.route('/unauthorized')
def unauthorized():
  """
  Returns unauthorized JSON when flask-login authentication fails
  """
  return {'errors': ['Unauthorized']}, 401


