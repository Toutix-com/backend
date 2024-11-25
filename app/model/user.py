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
    last_login = db.Column(db.DateTime, nullable=True)
    Token = db.Column(db.String(500), nullable=True)
    Birthday = db.Column(db.Date, nullable=True)
    Credit = db.Column(db.Integer, default=0)

    
    # Relationships
    tickets = db.relationship('Ticket', backref='user_tickets', lazy=True) # This is a one-to-many relationship, eg a user can have many tickets
    transactions_as_buyer = db.relationship('Transaction', foreign_keys='Transaction.BuyerID', backref='user_buyer', lazy=True) # This is a one-to-many relationship, eg a user can have many transactions as a buyer
    transactions_as_seller = db.relationship('Transaction', foreign_keys='Transaction.SellerID', backref='user_seller', lazy=True)   # This is a one-to-many relationship, eg a user can have many transactions as a seller
    paymentmethods = db.relationship('PaymentMethod', back_populates='users', lazy=True)   # This is a one-to-many relationship, eg a user can have many payment methods
    # payment_methods = db.relationship('PaymentMethod', backref='users', lazy=True)   # This is a one-to-many relationship, eg a user can have many payment methods
    selling_listings = db.relationship('MarketplaceListing', back_populates='sellers')

    def to_dict(self):
        return {
            'UserID': str(self.UserID),  # converting UUID to string for JSON compatibility
            'Email': self.Email,
            'FirstName': self.FirstName,
            'LastName': self.LastName,
            'Address': self.Address,
            'PhoneNumber': self.PhoneNumber,
            'tickets': [ticket.to_dict() for ticket in self.tickets] if self.tickets else [],
            'Birthday': self.Birthday.isoformat() if self.Birthday else None,  # Convert to ISO 8601 string format
            'Credit': self.Credit
            #'transactions_as_buyer': [transaction.to_dict() for transaction in self.transactions_as_buyer] if self.transactions_as_buyer else [],
            #'transactions_as_seller': [transaction.to_dict() for transaction in self.transactions_as_seller] if self.transactions_as_seller else [],
        }
    
    def get_id(self):
        return self.UserID




