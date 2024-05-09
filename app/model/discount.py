from . import db
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
from .ticket import Ticket

class Discount(db.Model):
    __tablename__ = 'discounts'

    DiscountID = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discount_type = db.Column(db.String(255), nullable=False)
    discount_value = db.Column(db.Float, nullable=False) #For percentage, use discount percentage. IE 10% = 0.1. For fixed amount, use discount amount. IE 10 = 10
    valid_from = db.Column(db.DateTime, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)
    usage_limit = db.Column(db.Integer, nullable=True)
    times_used = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'DiscountID': self.DiscountID,
            'discount_type': self.discount_type,
            'discount_value': self.discount_value,
            'valid_from': self.valid_from,
            'valid_until': self.valid_until,
            'usage_limit': self.usage_limit,
            'times_used': self.times_used
        }