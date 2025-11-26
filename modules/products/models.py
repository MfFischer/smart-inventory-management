
from modules.suppliers.models import Supplier
from flask_login import current_user
from sqlalchemy import UniqueConstraint
import uuid
from datetime import datetime
from inventory_system import db

from datetime import datetime
import uuid
from inventory_system import db

class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movements'

    movement_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id = db.Column(db.String(36), db.ForeignKey('products.product_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    movement_type = db.Column(db.String(50), nullable=False)  # 'stock_add', 'stock_remove', 'initial_stock', etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    product = db.relationship('Product', back_populates='movements')
    user = db.relationship('User', backref='inventory_movements')

    def __repr__(self):
        return f'<InventoryMovement {self.movement_id}: {self.movement_type} {self.quantity} units>'
class Product(db.Model):
    """Product model representing items in the inventory."""
    __tablename__ = 'products'

    product_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # UUID as primary key
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # Sales price
    cost_price = db.Column(db.Numeric(10, 2), nullable=False)  # COGS
    quantity_in_stock = db.Column(db.Integer, nullable=False, default=0)
    barcode = db.Column(db.String(100), unique=True, nullable=True)  # New barcode field
    reorder_point = db.Column(db.Integer, nullable=False, default=0)
    reorder_quantity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    # User-specific data segregation (ownership tracking)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_products_user_id'), nullable=True)

    __table_args__ = (
        UniqueConstraint('barcode', name='uq_products_barcode'),
    )

    # Define relationship to Supplier
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', name='fk_products_supplier_id'), nullable=True)
    supplier = db.relationship('Supplier', back_populates='products')

    # Define relationship to InventoryMovement
    movements = db.relationship(
        'InventoryMovement',
        back_populates='product',
        lazy='dynamic',
        cascade="all, delete-orphan"
    )

    def calculate_profit(self, quantity_sold):
        """Calculates profit for a given quantity sold."""
        total_revenue = self.price * quantity_sold
        total_cogs = self.cost_price * quantity_sold
        return total_revenue - total_cogs

    def to_dict(self):
        """Returns a dictionary representation of the Product model."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": str(self.price),
            "cost_price": str(self.cost_price),
            "quantity_in_stock": self.quantity_in_stock,
            "barcode": self.barcode,
            "reorder_point": self.reorder_point,
            "reorder_quantity": self.reorder_quantity,
            "supplier": self.supplier.name if self.supplier else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_id": self.user_id
        }

    @staticmethod
    def generate_sku(name):
        """Generate a simple SKU based on the product name and a unique identifier."""
        return f"{name[:3].upper()}-{uuid.uuid4().hex[:8]}"

    @classmethod
    def get_user_products(cls, user_id=None):
        user_id = user_id or current_user.id
        products = cls.query.filter_by(user_id=user_id).all()
        print("Products fetched:", [p.to_dict() for p in products])
        return products

    @classmethod
    def get_low_stock_alerts(cls, user_id=None):
        """Retrieve products below the reorder point, specific to a user or their hierarchy."""
        user_id = user_id or current_user.id
        if current_user.role == 'owner':
            return cls.query.filter(cls.user_id == user_id, cls.quantity_in_stock <= cls.reorder_point).all()
        return cls.query.filter(cls.user_id == current_user.parent_id, cls.quantity_in_stock <= cls.reorder_point).all()


# Define the reverse relationship in Supplier
Supplier.products = db.relationship(
    'Product', order_by=Product.product_id, back_populates='supplier')
