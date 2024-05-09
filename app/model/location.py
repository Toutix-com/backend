from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Location(db.Model):
    __tablename__ = 'locations'
    LocationID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name = db.Column(db.String(255))
    Address = db.Column(db.String(255))
    Capacity = db.Column(db.Integer)
    longitude = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.String(255), nullable=True)
    direction_url = db.Column(db.String(1000), nullable=True)
    events = db.relationship('Event', back_populates='location', lazy=True)  # This is a one-to-many relationship, eg a location can host many events

    def to_dict(self):
        return {
            'LocationID': str(self.LocationID),
            'Name': self.Name,
            'Address': self.Address,
            'Capacity': self.Capacity,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'direction_url': self.direction_url
            # 'events': removed to prevent recursion
        }
        '''if include_events:
            location_dict['events'] = [event.to_dict(include_location=False) for event in self.events] if self.events else []
        return location_dict'''
