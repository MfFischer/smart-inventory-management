from inventory_system import db
from datetime import datetime


class Business(db.Model):
    __tablename__ = 'business'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    vat_id = db.Column(db.String(50))
    vat_rate = db.Column(db.Float, default=0.0)  # Added VAT rate field
    email = db.Column(db.String(120))
    website = db.Column(db.String(120))
    logo_path = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with User
    user = db.relationship('User', backref='business', uselist=False)

    def __repr__(self):
        return f'<Business {self.name}>'