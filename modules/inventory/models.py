from inventory_system import db
from flask_login import current_user
from datetime import datetime


class Inventory(db.Model):
    __tablename__ = 'inventory'

    # Primary key for the Inventory table
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key reference to the Products table with UUID
    product_id = db.Column(db.String(36), db.ForeignKey('products.product_id'), nullable=False)

    # Relationship with Product
    product = db.relationship('Product', backref='inventory_items')

    # Foreign key reference to the Suppliers table (optional)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    supplier = db.relationship('Supplier', backref='supplier_inventory_link')

    # Foreign key reference to the Users table for data segregation
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Stock Keeping Unit (SKU) for the product
    sku = db.Column(db.String(100), nullable=False, unique=True)

    # Quantity of stock available
    stock_quantity = db.Column(db.Integer, default=0)

    # Threshold for when to reorder stock
    reorder_threshold = db.Column(db.Integer, default=0)

    # Unit price of the product (sales price)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    # Cost price of the product (COGS)
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)

    # Timestamp when the record was created
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Timestamp when the record was last updated
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    last_reordered_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "supplier_id": self.supplier_id,
            "sku": self.sku,
            "stock_quantity": self.stock_quantity,
            "reorder_threshold": self.reorder_threshold,
            "unit_price": str(self.unit_price),
            "cost_price": str(self.cost_price),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_reordered_at": self.last_reordered_at,
            "product_name": self.product.name if self.product else "Unknown",
            "user_id": self.user_id
        }

    @classmethod
    def get_user_inventory(cls, user_id=None):
        """Retrieve inventory specific to a user or their hierarchy."""
        user_id = user_id or current_user.id  # Default to current logged-in user
        print(f"Fetching inventory for user ID: {user_id}, role: {current_user.role}")

        if current_user.role == 'admin':
            inventory_items = cls.query.filter_by(user_id=user_id).all()
            print(f"Inventory items for admin: {inventory_items}")
            return inventory_items

        # Hierarchical access for staff of the owner
        inventory_items = cls.query.filter_by(user_id=current_user.parent_id).all()
        print(f"Inventory items for staff under user ID {current_user.parent_id}: {inventory_items}")
        return inventory_items

    @classmethod
    def get_low_stock_alerts(cls, user_id=None):
        """Retrieve inventory items below the reorder threshold for a specific user or their hierarchy."""
        user_id = user_id or current_user.id
        if current_user.role == 'admin':
            return cls.query.filter(cls.user_id == user_id, cls.stock_quantity <= cls.reorder_threshold).all()
        return cls.query.filter(cls.user_id == current_user.parent_id,
                                cls.stock_quantity <= cls.reorder_threshold).all()
