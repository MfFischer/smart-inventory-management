from inventory_system import db
from marshmallow import Schema, fields, validate, validates, ValidationError


# Define the Supplier model representing the 'suppliers' table in the database
class Supplier(db.Model):
    __tablename__ = 'suppliers'

    # Primary key for the Supplier table
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Supplier name (required)
    name = db.Column(db.String(255), nullable=False)

    # Optional phone number
    phone = db.Column(db.String(20), nullable=True)

    # Optional email address
    email = db.Column(db.String(255), nullable=False, unique=True)

    # Optional address field
    address = db.Column(db.Text, nullable=True)

    # Timestamps for record creation and last update
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    @validates('name')
    def validate_name(self, value):
        if not value or value.strip() == '':
            raise ValidationError("Supplier name must not be empty or contain only whitespace.")

    # Convert model instance to dictionary format
    def to_dict(self):
        """Convert the Supplier object to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

