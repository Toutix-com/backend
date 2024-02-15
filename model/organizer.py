from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Organizer(db.Model):
    __tablename__ = 'organizers'
    OrganizerID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name = db.Column(db.String(255))
    ContactInfo = db.Column(db.String(255))

    events = db.relationship('Event', back_populates='organizer')

    def to_dict(self):
        return {
            'OrganizerID': str(self.OrganizerID), 
            'Name': self.Name,
            'ContactInfo': self.ContactInfo,
            'events': [event.to_dict() for event in self.events] if self.events else [],
        }

