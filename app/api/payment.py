'''import stripe
from flask import Blueprint, request, jsonify
from app.model import PaymentMethod, db
from flask_jwt_extended import jwt_required
from app.config import STRIPE_SECRET_KEY

payment_routes = Blueprint('payment', __name__)

stripe.api_key = STRIPE_SECRET_KEY

@payment_routes.route('/charge', methods=['POST'])
@jwt_required
def charge():
    data = request.get_json()
    amount = data.get('amount')
    currency = data.get('currency', 'usd')
    source = data.get('source')

    if not amount or not source:
        return jsonify({"error": "Amount and source are required."}), 400

    try:
        charge = stripe.Charge.create(
            amount=amount,
            currency=currency,
            source=source,
        )
        # Save the charge.id in your database for future reference
        payment_method = PaymentMethod(PaymentDetails=charge.id)
        db.session.add(payment_method)
        db.session.commit()
        return jsonify({"success": True, "charge": charge.id}), 200
    except stripe.error.StripeError as e:
        return jsonify({"error": str(e)}), 400'''