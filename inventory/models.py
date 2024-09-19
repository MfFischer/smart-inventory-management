from inventory_system import db


class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    sku = db.Column(db.String(100), nullable=False, unique=True)
    stock_quantity = db.Column(db.Integer, default=0)
    reorder_threshold = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    product = db.relationship('Product', backref='inventory')
    supplier = db.relationship('Supplier', backref='inventory')

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "sku": self.sku,
            "stock_quantity": self.stock_quantity,
            "reorder_threshold": self.reorder_threshold,
            "unit_price": self.unit_price,
            "supplier_id": self.supplier_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
