from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID,ENUM
import enum

class StatusEnum(enum.Enum):
    Available      = 'available'
    Sold      = 'sold'
    ListedonMarketplace = 'listedonmarketplace'
    Admitted        = 'admitted'

class Ticket(db.Model):
    __tablename__ = 'tickets'
    TicketID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    UserID = db.Column(UUID(as_uuid=True), db.ForeignKey('users.UserID'))
    SeatNumber = db.Column(db.String(255), nullable=True)
    initialPrice = db.Column(db.Numeric(10, 2))
    Price = db.Column(db.Numeric(10, 2))
    Status = db.Column(db.Enum(StatusEnum,name='Status'))
    EventID = db.Column(UUID(as_uuid=True), db.ForeignKey('events.EventID'))
    TransactionID = db.Column(UUID(as_uuid=True), db.ForeignKey('transactions.TransactionID'))
    Category = db.Column(db.String(255))
    CreationDate = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship('User', back_populates='tickets')
    transactions = db.relationship('Transaction', back_populates='tickets') # Singular, assuming one-to-many from Transaction to Ticket
    marketplace_listings = db.relationship('MarketplaceListing', back_populates='tickets')
    event = db.relationship('Event', back_populates='tickets', lazy=True)

    def to_dict(self):
        return {
            "TicketID": str(self.TicketID),  
            "UserID": str(self.UserID) if self.UserID else None,  
            "SeatNumber": self.SeatNumber,
            "InitialPrice": str(self.initialPrice),  
            "Price": str(self.Price),
            "Status": self.Status.name if self.Status else None,  # Access Enum value name
            "Category": self.Category
        }