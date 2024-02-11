from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Location(db.Model):
    __tablename__ = 'locations'
    LocationID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name = db.Column(db.String(255))
    Address = db.Column(db.String(255))
    Capacity = db.Column(db.Integer)

    # Relationships
    events = db.relationship('Event', back_populates='location')

    def to_dict(self):
    return {
        'LocationID': str(self.LocationID),  # Convert UUID to string for JSON compatibility
        'Name': self.Name,
        'Address': self.Address,
        'Capacity': self.Capacity,
        'events': [event.to_dict() for event in self.events] if self.events else [],
    }
