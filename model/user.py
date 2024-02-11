from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class User(db.Model):
    __tablename__ = 'users'
    UserID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Email = db.Column(db.String(255), nullable=False)
    Address = db.Column(db.String(255), nullable=True)
    PhoneNumber = db.Column(db.String(20), nullable=True)
    FirstName = db.Column(db.String(255), nullable=True)
    LastName = db.Column(db.String(255), nullable=True)
    OTP = db.Column(db.String(6), nullable=True)  # Assuming OTPs are 6 digits
    otp_expiry = db.Column(db.Integer, nullable=True)
    # Create last login, update with access token

    # Relationships
    tickets = db.relationship('Ticket', backref='user', lazy=True) # This is a one-to-many relationship, eg a user can have many tickets
    transactions_as_buyer = db.relationship('Transaction', foreign_keys='Transaction.BuyerID', backref='buyer', lazy=True) # This is a one-to-many relationship, eg a user can have many transactions as a buyer
    transactions_as_seller = db.relationship('Transaction', foreign_keys='Transaction.SellerID', backref='seller', lazy=True)   # This is a one-to-many relationship, eg a user can have many transactions as a seller
    payment_methods = db.relationship('PaymentMethod', backref='user', lazy=True)   # This is a one-to-many relationship, eg a user can have many payment methods

    def to_dict(self):
        return {
            'UserID': str(self.UserID),  # converting UUID to string for JSON compatibility
            'Email': self.Email,
            'FirstName': self.FirstName,
            'LastName': self.LastName,
            'Address': self.Address,
            'PhoneNumber': self.PhoneNumber,
            'tickets': [ticket.to_dict() for ticket in self.tickets] if self.tickets else [],
            #'transactions_as_buyer': [transaction.to_dict() for transaction in self.transactions_as_buyer] if self.transactions_as_buyer else [],
            #'transactions_as_seller': [transaction.to_dict() for transaction in self.transactions_as_seller] if self.transactions_as_seller else [],
        }




