from .OTP import OTPManager
from flask import Blueprint, request, jsonify
from app.model import User, db
from flask_login import current_user, login_user, logout_user, login_required
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import time

#write blueprint
auth_routes = Blueprint('auth', __name__)

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
    is_social_login = data.get('is_social_login')
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    if not email:
        return jsonify({"error": "Email is required."}), 400

    if is_social_login:
        user = User.query.filter_by(Email=email).first()
        if not user:
            # Create a new user
            user = User(Email=email, FirstName=first_name, LastName=last_name)
            db.session.add(user)
            db.session.commit()

        # Determine if it's the user's first login
        first_time_login = user.last_login is None

        # Update last login time to current datetime
        user.last_login = datetime.utcnow()

        # Generate access token
        otp_manager = OTPManager(email)
        access_token = otp_manager.generate_access_token(identity=email)

        # Store the access token in the user's record
        user.Token = access_token
        db.session.commit()

        login_user(user, force=True)

        first_name = user.FirstName
        last_name = user.LastName

        # Return access token, email, and first_time_login boolean
        return jsonify({
            "access_token": access_token,
            "email": user.Email,
            "first_time_login": first_time_login,
            "user_id": user.UserID,
            "message": "You are logged in.",
            "social_login": True,
            "first_name": first_name,
            "last_name": last_name  
        }), 200
    else:
        otp_manager = OTPManager(email)
        otp_manager.generate_store_otp()
        send_otp = otp_manager.send_otp()
        if send_otp:
            return send_otp
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
    
    # Determine if it's the user's first login
    first_time_login = user.last_login is None

    # Update last login time to current datetime
    user.last_login = datetime.utcnow()

    # Get access token
    access_token = user.Token

    # Update last_login in the database
    db.session.commit()

    login_user(user, force=True)

    first_name = user.FirstName
    last_name = user.LastName

    # Return access token, email, and first_time_login boolean
    return jsonify({
        "access_token": access_token,
        "email": user.Email,
        "first_time_login": first_time_login,
        "user_id": user.UserID,
        "message": "You are logged in.",
        "first_name": first_name,
        "last_name": last_name  
    }), 200

@auth_routes.route('/unauthorized')
def unauthorized():
  """
  Returns unauthorized JSON when flask-login authentication fails
  """
  return {'errors': ['Unauthorized']}, 401


