from inventory_system import db


class Sale(db.Model):
    __tablename__ = 'sales'

    # Define table columns with appropriate data types and constraints
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_status = db.Column(db.String(50), default='completed')

    # Track record creation and update timestamps
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    # Define relationship with the Product model
    product = db.relationship('Product', backref='sales')

    def to_dict(self):
        """
        Convert the Sale model instance to a dictionary representation.
        """
        return {
            "id": self.id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "total_price": self.total_price,
            "sale_status": self.sale_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
