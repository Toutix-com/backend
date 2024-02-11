from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
from .ticket import Ticket

class Event(db.Model):
    __tablename__ = 'events'

    EventID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name = db.Column(db.String(255), nullable=False)
    Description = db.Column(db.Text, nullable=True)
    LocationID = db.Column(UUID(as_uuid=True), db.ForeignKey('locations.LocationID'), nullable=False)
    DateTime = db.Column(db.DateTime, nullable=False)
    EndTime = db.Column(db.DateTime, nullable=True)
    OrganizerID = db.Column(UUID(as_uuid=True), db.ForeignKey('organizers.OrganizerID'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)


    # Relationships
    location = db.relationship('Location', backref='event', lazy=True) # This is a one-to-one relationship, eg an event has one location
    tickets = db.relationship('Ticket', backref='event', lazy=True) # This is a one-to-many relationship, eg an event can have many tickets
    organizer = db.relationship('Organizer', backref='event', lazy=True) # This is a one-to-one relationship, eg an event has one organizer
    transactions = db.relationship('Transaction', backref='event', lazy=True) # This is a one-to-many relationship, eg an event can have many transactions
    marketplace_listings = db.relationship('MarketplaceListing', back_populates='event') # This is a one-to-many relationship, eg an event can have many marketplace listing
    
    
    def to_dict(self):
    return {
        'EventID': str(self.EventID),  # Convert UUID to string for JSON compatibility
        'Name': self.Name,
        'Description': self.Description,
        'image_url': self.image_url,
        'DateTime': self.DateTime.isoformat() if self.DateTime else None,  # Convert to ISO 8601 string
        'EndTime': self.EndTime.isoformat() if self.EndTime else None,  # Convert to ISO 8601 string
        'location': self.location.to_dict() if self.location else None,
        'starting_price': db.session.query(func.min(Ticket.Price)).filter(Ticket.EventID == self.EventID).scalar(),
        'max_tickets_per_user': 4,  # Replace with the other value if neccesary
        'remaining_tickets': Ticket.query.filter_by(EventID=self.EventID, Status='Available').count(),
        'total_tickets': Ticket.query.filter_by(EventID=self.EventID).count(),
    }
