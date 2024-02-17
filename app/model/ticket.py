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
    SeatNumber = db.Column(db.String(255))
    initialPrice = db.Column(db.Numeric(10, 2))
    Price = db.Column(db.Numeric(10, 2))
    Status = db.Column(db.Enum(StatusEnum,name='Status'))

    user = db.relationship('User', back_populates='tickets')
    transactions = db.relationship('Transaction', back_populates='tickets')
    marketplace_listings = db.relationship('MarketplaceListing', back_populates='tickets')

    def to_dict(self):
        return {
            "TicketID": str(self.TicketID),  
            "UserID": str(self.UserID) if self.UserID else None,  # Handle nullable UserID
            "SeatNumber": self.SeatNumber,
            "InitialPrice": str(self.initialPrice),  # Convert numeric to string if necessary
            "Price": str(self.Price),
            "Status": self.Status.name if self.Status else None  # Access Enum value name
        }