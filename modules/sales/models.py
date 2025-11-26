from inventory_system import db
from decimal import Decimal
from flask_login import current_user
from datetime import datetime
import uuid


class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    receipt_number = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    total_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    profit = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    discount_percentage = db.Column(db.Float, default=0.0)
    sale_status = db.Column(db.String(50), default='pending')  # Changed default to 'pending'
    customer_name = db.Column(db.String(255), nullable=True)
    sale_date = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    sale_items = db.relationship('SaleItem', back_populates='sale', cascade="all, delete-orphan")

    def calculate_total_price_and_profit(self):
        """
        Calculate the total price and profit for the sale based on individual items.
        """
        total_price = Decimal('0')
        total_cost = Decimal('0')

        for item in self.sale_items:
            item_total = item.calculate_discounted_price()
            total_price += item_total["discounted_price"]
            total_cost += Decimal(str(item.product.cost_price)) * Decimal(str(item.quantity))

        self.total_price = total_price
        self.profit = total_price - total_cost
        return self

    def to_dict(self):
        """
        Convert the Sale model instance to a dictionary representation.
        """
        return {
            "id": self.id,
            "receipt_number": self.receipt_number,
            "sale_items": [{
                "id": item.id,
                "product": {
                    "name": item.product.name,
                    "price": float(item.price_per_unit)
                },
                "quantity": item.quantity,
                "price_per_unit": float(item.price_per_unit),
                "discount_percentage": item.discount_percentage,
                "total": float(item.calculate_discounted_price()["discounted_price"])
            } for item in self.sale_items],
            "total_price": float(self.total_price),
            "profit": float(self.profit),
            "discount_percentage": self.discount_percentage,
            "sale_status": self.sale_status,
            "customer_name": self.customer_name
        }

    @classmethod
    def get_pending_sale(cls, user_id=None):
        """Get or create a pending sale for the user."""
        user_id = user_id or current_user.id
        sale = cls.query.filter_by(
            user_id=user_id,
            sale_status='pending'
        ).first()

        if not sale:
            sale = cls(
                user_id=user_id,
                sale_status='pending',
                customer_name="Pending Sale",
                total_price=0,
                profit=0
            )
            db.session.add(sale)
            db.session.commit()

        return sale

    @classmethod
    def create_from_barcode(cls, barcode, quantity=1, user_id=None):
        """
        Create or update a sale item from a scanned barcode.
        """
        from modules.products.models import Product

        product = Product.query.filter_by(barcode=barcode).first()
        if not product:
            raise ValueError(f"Product with barcode {barcode} not found")

        if product.quantity_in_stock < quantity:
            raise ValueError(f"Insufficient stock for {product.name} (Available: {product.quantity_in_stock})")

        # Get or create pending sale
        sale = cls.get_pending_sale(user_id)

        # Check if product already exists in sale
        existing_item = next(
            (item for item in sale.sale_items if item.product_id == product.product_id),
            None
        )

        if existing_item:
            if product.quantity_in_stock < (existing_item.quantity + quantity):
                raise ValueError(f"Insufficient stock for {product.name}")
            existing_item.quantity += quantity
        else:
            sale_item = SaleItem(
                product_id=product.product_id,
                quantity=quantity,
                price_per_unit=product.price,
                discount_percentage=0.0
            )
            sale.sale_items.append(sale_item)

        sale.calculate_total_price_and_profit()
        db.session.commit()
        return sale

    def complete_sale(self, customer_name=None):
        """
        Complete the sale by updating status and deducting stock.
        """
        if customer_name:
            self.customer_name = customer_name

        for item in self.sale_items:
            item.deduct_stock()

        self.sale_status = 'completed'
        self.sale_date = datetime.now()
        db.session.commit()
        return self


class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percentage = db.Column(db.Float, default=0.0)

    # Relationships
    sale = db.relationship('Sale', back_populates='sale_items')
    product = db.relationship('Product')

    def calculate_discounted_price(self):
        """
        Calculate the price of this sale item after applying the discount.
        """
        base_price = Decimal(str(self.price_per_unit)) * Decimal(str(self.quantity))
        if self.discount_percentage:
            discount = Decimal(str(self.discount_percentage)) / Decimal('100')
            discount_amount = base_price * discount
            discounted_price = base_price - discount_amount
        else:
            discounted_price = base_price

        return {"discounted_price": discounted_price}

    def deduct_stock(self):
        """
        Deduct the stock of the product when the sale is completed.
        """
        if not self.product:
            raise ValueError("Product not found")

        if self.product.quantity_in_stock < self.quantity:
            raise ValueError(f"Insufficient stock for {self.product.name}")

        self.product.quantity_in_stock -= self.quantity
        db.session.commit()

    def to_dict(self):
        """
        Convert the SaleItem instance to a dictionary representation.
        """
        result = self.calculate_discounted_price()
        return {
            "id": self.id,
            "product": {
                "id": self.product_id,
                "name": self.product.name,
                "price": float(self.price_per_unit)
            },
            "quantity": self.quantity,
            "price_per_unit": float(self.price_per_unit),
            "discount_percentage": self.discount_percentage,
            "total": float(result["discounted_price"])
        }