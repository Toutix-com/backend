from flask import Blueprint
from .auth import auth_routes
from .user_routes import user_routes
from .event_routes import event_routes
from .OTP import otp_routes
from .location_routes import location_routes
#from .payment import payment_routes

api = Blueprint('api', __name__)

api.register_blueprint(auth_routes, url_prefix='/auth')
api.register_blueprint(user_routes, url_prefix='/user')
api.register_blueprint(event_routes, url_prefix='/events')
api.register_blueprint(otp_routes, url_prefix='/otp')
api.register_blueprint(location_routes, url_prefix='/locations')
api.register_blueprint(payment_routes, url_prefix='/payment')