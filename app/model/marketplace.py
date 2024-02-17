from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class MarketplaceListing(db.Model):
    __tablename__ = 'marketplacelistings'
    ListingID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    TicketID = db.Column(UUID(as_uuid=True), db.ForeignKey('tickets.TicketID'))
    SellerID = db.Column(UUID(as_uuid=True), db.ForeignKey('users.UserID'))
    EventID = db.Column(UUID(as_uuid=True), db.ForeignKey('events.EventID'))

    tickets = db.relationship('Ticket', back_populates='marketplace_listings')
    sellers = db.relationship('User', back_populates='selling_listings')
    events = db.relationship('Event', back_populates='marketplace_listings')

    def to_dict(self):
        return {
            'ListingID': str(self.ListingID),  # Convert UUID to string for JSON compatibility
            'TicketID': str(self.TicketID),  # Ensuring foreign key is also string for JSON
            'SellerID': str(self.SellerID),  # Ensuring foreign key is also string for JSON
            'ticket_details': self.ticket.to_dict() if self.ticket else None,
            'event_details': self.event.to_dict() if self.event else None,
        }