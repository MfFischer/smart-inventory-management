from inventory_system import db

# Inventory model to represent stock information in the database
class Inventory(db.Model):
    __tablename__ = 'inventory'

    # Primary key for the Inventory table
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Foreign key reference to the Products table
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    # create the relationship with Product
    product = db.relationship('Product', backref='inventory_items')

    # Foreign key reference to the Suppliers table (optional)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    # Updated to match the new backref name in the Supplier model
    supplier = db.relationship('Supplier', backref='supplier_inventory_link')

    # Stock Keeping Unit (SKU) for the product
    sku = db.Column(db.String(100), nullable=False, unique=True)

    # Quantity of stock available
    stock_quantity = db.Column(db.Integer, default=0)

    # Threshold for when to reorder stock
    reorder_threshold = db.Column(db.Integer, default=0)

    # Unit price of the product
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    # Timestamp when the record was created
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Timestamp when the record was last updated
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    last_reordered_at = db.Column(db.DateTime, nullable=True)

    # Convert object to a dictionary format for easy JSON serialization
    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "supplier_id": self.supplier_id,
            "sku": self.sku,
            "stock_quantity": self.stock_quantity,
            "reorder_threshold": self.reorder_threshold,
            "unit_price": str(self.unit_price),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "product_name": self.product.name if self.product else "Unknown"
        }
