from inventory_system import db
from datetime import datetime


class Category(db.Model):
    """Category model representing user-defined categories for expenses."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    type = db.Column(db.String(20), default='expense')  # New field to distinguish expense/income categories

    def to_dict(self):
        """Convert the Category instance to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type
        }


class Expense(db.Model):
    """Expense model to track various business expenses linked to a category."""
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date_incurred = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    expense_type = db.Column(db.String(20), default='regular')  # New field to distinguish regular/other expenses
    reference_number = db.Column(db.String(50))  # New field
    payment_status = db.Column(db.String(20), default='paid')  # New field

    category = db.relationship("Category", backref="expenses")

    def to_dict(self):
        """Convert the Expense instance to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "description": self.description,
            "amount": self.amount,
            "date_incurred": self.date_incurred,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "category_name": self.category.name,
            "expense_type": self.expense_type,
            "reference_number": self.reference_number,
            "payment_status": self.payment_status
        }


class OtherIncome(db.Model):
    """Model for tracking miscellaneous income sources."""
    __tablename__ = 'other_income'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date_received = db.Column(db.DateTime, default=datetime.now)
    reference_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    category = db.relationship("Category", backref="income_entries")

    def to_dict(self):
        """Convert the OtherIncome instance to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "description": self.description,
            "amount": self.amount,
            "date_received": self.date_received,
            "reference_number": self.reference_number,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "category_name": self.category.name
        }

    @staticmethod
    def get_income_categories():
        """Get predefined income categories."""
        return [
            'interest_income',
            'rental_income',
            'commission_income',
            'service_fees',
            'miscellaneous_income',
            'asset_sale',
            'insurance_claims',
            'rebates',
            'other'
        ]
