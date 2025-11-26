from inventory_system import db
from datetime import datetime


class AccountsReceivable(db.Model):
    __tablename__ = 'accounts_receivable'

    # Define table columns with appropriate data types and constraints
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False, unique=True)
    customer_name = db.Column(db.String(255), nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    amount_due = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')  # Tracks if the payment is pending or partially paid
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # User-specific
    notes = db.Column(db.String(255), nullable=True)  # Optional notes regarding the receivable

    # Track record creation and update timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    # Define relationship with the Sale model
    sale = db.relationship('Sale', backref='accounts_receivable')  # Relationship to Sale
    user = db.relationship('User', backref='accounts_receivables')  # Relationship to User


def to_dict(self):
        """
        Convert the AccountsReceivable model instance to a dictionary representation.
        """
        return {
            "id": self.id,
            "sale_id": self.sale_id,
            "customer_name":self.customer_name,
            "due_date": self.due_date,
            "amount_due": self.amount_due,
            "status": self.status,
            "user": self.user_id,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
