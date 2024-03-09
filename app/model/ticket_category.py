from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID

class TicketCategory(db.Model):
    __tablename__ = 'ticket_categories'

    CategoryID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    max_limit = db.Column(db.Integer, nullable=False)
    ticket_sold = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=True)
    EventID = db.Column(UUID(as_uuid=True), db.ForeignKey('events.EventID'), nullable=False)

    event = db.relationship('Event', back_populates='ticket_categories')
    tickets = db.relationship('Ticket', back_populates='ticket_categories', lazy=True)

    def to_dict(self):
        return {
            'CategoryID': str(self.CategoryID), 
            'name': self.name,
            'price': self.price,
            'max_limit': self.max_limit,
            'ticket_sold': self.ticket_sold,
            'description': self.description
        }