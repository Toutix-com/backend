from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Transaction(db.Model):
    __tablename__ = 'transactions'
    TransactionID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    TicketID = db.Column(UUID(as_uuid=True), db.ForeignKey('tickets.TicketID'))
    BuyerID = db.Column(UUID(as_uuid=True), db.ForeignKey('users.UserID'))
    SellerID = db.Column(UUID(as_uuid=True), db.ForeignKey('users.UserID'))
    PaymentMethodID = db.Column(UUID(as_uuid=True), db.ForeignKey('paymentmethods.PaymentMethodID'))
    TransactionAmount = db.Column(db.Numeric(10, 2))
    TransactionDate = db.Column(db.DateTime)

    ticket = db.relationship('Ticket', back_populates='transactions')
    buyer = db.relationship('User', foreign_keys=[BuyerID], back_populates='transactions_as_buyer')
    seller = db.relationship('User', foreign_keys=[SellerID], back_populates='transactions_as_seller')
    payment_method = db.relationship('PaymentMethod', back_populates='transactions')

    def to_dict(self):
        """Serialize transaction to a dict for easier JSON output."""
        return {
            'TransactionID': str(self.TransactionID),  # Convert UUID to string for JSON compatibility
            'TicketID': str(self.TicketID),
            'BuyerID': str(self.BuyerID),
            'SellerID': str(self.SellerID),
            'PaymentMethodID': str(self.PaymentMethodID),
            'TransactionAmount': str(self.TransactionAmount),  # Convert numeric to string if necessary, or keep as is for JSON serialization
            'TransactionDate': self.TransactionDate.isoformat() if self.TransactionDate else None,  # Convert datetime to ISO 8601 string format
            #'ticket': self.ticket.to_dict() if self.ticket else None,
            #'buyer': {'BuyerID': str(self.BuyerID), 'FirstName': self.buyer.FirstName, 'LastName': self.buyer.LastName} if self.buyer else None,
            #'seller': {'SellerID': str(self.SellerID), 'FirstName': self.seller.FirstName, 'LastName': self.seller.LastName} if self.seller else None,
            #'payment_method': self.payment_method.to_dict() if self.payment_method else None,
        }