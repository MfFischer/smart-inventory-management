from datetime import datetime
from inventory_system import db
from marshmallow import validates, ValidationError
from flask_login import current_user
from modules.users.models import User


class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(255), nullable=True)  # Optional contact field for supplier
    description = db.Column(db.Text, nullable=True)  # Optional description field
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(255), nullable=False, unique=True)  # Required, unique email
    address = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    @validates('name')
    def validate_name(self, value):
        """Ensure that the supplier name is not empty or whitespace only."""
        if not value or value.strip() == '':
            raise ValidationError("Supplier name must not be empty or contain only whitespace.")
        return value

    @validates('email')
    def validate_email(self, value):
        """Ensure that the email field is not empty and follows a basic format."""
        if not value or value.strip() == '':
            raise ValidationError("Supplier email must not be empty.")
        if '@' not in value or '.' not in value:
            raise ValidationError("Invalid email format.")
        return value

    def to_dict(self):
        """Return a dictionary representation of the Supplier model."""
        return {
            'id': self.id,
            'name': self.name,
            'contact': self.contact,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id
        }

    @classmethod
    def get_user_suppliers(cls, user_id=None):
        """
        Retrieve suppliers specific to a user or their hierarchy.
        """
        user_id = user_id or current_user.id
        if current_user.role == 'owner':
            return cls.query.filter_by(user_id=user_id).all()
        # Hierarchical access for staff under the owner's account
        return cls.query.filter_by(user_id=current_user.parent_id).all()


class AccountsPayable(db.Model):
    """
    Model for tracking accounts payable entries for suppliers.
    """
    __tablename__ = 'accounts_payable'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Note: matches User.__tablename__
    amount_due = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='unpaid')
    paid_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.now,
        onupdate=datetime.now
    )

    # Relationships
    supplier = db.relationship('Supplier', backref=db.backref('accounts_payable', lazy=True))
    user = db.relationship('User', backref=db.backref('accounts_payable', lazy=True))

    def to_dict(self):
        """Convert the AccountsPayable object to a dictionary."""
        return {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'user_id': self.user_id,
            'amount_due': self.amount_due,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<AccountsPayable {self.id} - Amount: {self.amount_due} - Due: {self.due_date}>'
