from inventory_system import db


# Define the Supplier model representing the 'suppliers' table in the database
class Supplier(db.Model):
    __tablename__ = 'suppliers'

    # Primary key column with auto-increment
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Supplier name (required)
    name = db.Column(db.String(255), nullable=False)

    # Optional phone number
    phone = db.Column(db.String(20), nullable=True)

    # Optional email address
    email = db.Column(db.String(255), nullable=True)

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

    # Convert model instance to dictionary format
    def to_dict(self):
        """Returns a dictionary representation of the Supplier instance."""
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
