from inventory_system import db
from marshmallow import validates, ValidationError

# Define the Supplier model representing the 'suppliers' table in the database
class Supplier(db.Model):
    __tablename__ = 'suppliers'
    __table_args__ = {'extend_existing': True}

    # Primary key for the Supplier table
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Supplier name (required)
    name = db.Column(db.String(255), nullable=False)

    # Optional phone number for the supplier
    phone = db.Column(db.String(20), nullable=True)

    # Email address (required and must be unique)
    email = db.Column(db.String(255), nullable=False, unique=True)

    # Optional address field for supplier's location
    address = db.Column(db.Text, nullable=True)

    # Timestamps: created_at for record creation, updated_at for the last update
    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    # Validate the 'name' field to ensure it's not empty or only whitespace
    @validates('name')
    def validate_name(self, value):
        if not value or value.strip() == '':
            raise ValidationError(
                "Supplier name must not be empty or contain only whitespace."
            )

    # Convert model instance to dictionary format for easier data handling
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
