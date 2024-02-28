from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class PaymentMethod(db.Model):
    __tablename__ = 'paymentmethods'
    PaymentMethodID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    UserID = db.Column(UUID(as_uuid=True), db.ForeignKey('users.UserID'))
    Provider = db.Column(db.String(255))
    PaymentDetails = db.Column(db.Text)

    users = db.relationship('User', back_populates='paymentmethods')
    #transactions = db.relationship('Transaction', back_populates='paymentmethods')

    def to_dict(self):
        return {
            'PaymentMethodID': str(self.PaymentMethodID),  # Convert UUID to string for JSON compatibility
            'UserID': str(self.UserID),
            'Provider': self.Provider,
            'PaymentDetails': self.PaymentDetails,  # Consider excluding or anonymizing sensitive details
            # Relationships - Consider what's necessary for your application
            #'user': {'UserID': str(self.UserID), 'FirstName': self.user.FirstName, 'LastName': self.user.LastName} if self.user else None,
            # For transactions, consider whether you need to include detailed transaction information here
            # Including a list of transaction IDs could be useful without overwhelming the response
            #'transactions': [{'TransactionID': str(transaction.TransactionID)} for transaction in self.transactions] if self.transactions else [],
        }