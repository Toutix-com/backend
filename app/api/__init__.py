from flask import Blueprint
from .auth import auth_routes
from .user_routes import user_routes
from .event_routes import event_routes
from .OTP import otp_routes
from .location_routes import location_routes
from .payment_routes import payment_routes
from .ticket_manager import ticket_routes
from .market_routes import market_routes
from .organiser_routes import organiser_routes
from .scanner_app import validater_routes


api = Blueprint('api', __name__)

api.register_blueprint(auth_routes, url_prefix='/auth')
api.register_blueprint(user_routes, url_prefix='/user')
api.register_blueprint(event_routes, url_prefix='/events')
api.register_blueprint(otp_routes, url_prefix='/otp')
api.register_blueprint(location_routes, url_prefix='/locations')
api.register_blueprint(payment_routes, url_prefix='/payment')
api.register_blueprint(ticket_routes, url_prefix='/ticket')
api.register_blueprint(market_routes, url_prefix='/market')
api.register_blueprint(organiser_routes, url_prefix='/organiser')
api.register_blueprint(validater_routes, url_prefix='/validater')

