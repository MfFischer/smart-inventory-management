from inventory_system import db
from suppliers.models import Supplier  # Import Supplier from the suppliers module

class InventoryMovement(db.Model):
    """Inventory Movement model representing stock in/out records."""
    __tablename__ = 'inventory_movements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    movement_type = db.Column(db.String(50), nullable=False)  # e.g., 'stock_in', 'stock_out'
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Define relationship to Product
    product = db.relationship('Product', back_populates='movements')

class Product(db.Model):
    """Product model representing items in the inventory."""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity_in_stock = db.Column(db.Integer, nullable=False, default=0)
    reorder_point = db.Column(db.Integer, nullable=False, default=0)
    reorder_quantity = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    # Define relationship to Supplier
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    supplier = db.relationship('Supplier', back_populates='products')

    # Define relationship to InventoryMovement
    movements = db.relationship('InventoryMovement', back_populates='product', lazy='dynamic')

    def to_dict(self):
        """Returns a dictionary representation of the Product model."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": str(self.price),
            "quantity_in_stock": self.quantity_in_stock,
            "reorder_point": self.reorder_point,
            "reorder_quantity": self.reorder_quantity,
            "supplier": self.supplier.name if self.supplier else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

Supplier.products = db.relationship('Product', order_by=Product.id, back_populates='supplier')
