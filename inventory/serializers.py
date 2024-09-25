from marshmallow import Schema, fields, validate, validates, ValidationError
from inventory.models import Inventory, Inventory  # Ensure Inventory and InventoryMovement models are imported
from products.models import Product
from suppliers.models import Supplier


# Serializer for Inventory model
class InventorySchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)
    supplier_id = fields.Int(required=True)
    sku = fields.Str(required=True, validate=validate.Length(max=100))
    stock_quantity = fields.Int(required=True)
    reorder_threshold = fields.Int(required=True)
    unit_price = fields.Decimal(required=True, as_string=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # Validate product_id to ensure it exists
    @validates('product_id')
    def validate_product_id(self, value):
        if not Product.query.get(value):
            raise ValidationError("Invalid product_id. Product does not exist.")

    # Validate supplier_id to ensure it exists
    @validates('supplier_id')
    def validate_supplier_id(self, value):
        if not Supplier.query.get(value):
            raise ValidationError("Invalid supplier_id. Supplier does not exist.")


# Serializer for InventoryMovement model
class InventoryMovementSchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    movement_type = fields.Str(required=True, validate=validate.OneOf(['in', 'out']))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('product_id')
    def validate_product_id(self, value):
        # Check if the product exists before creating an inventory movement
        if not Product.query.get(value):
            raise ValidationError("Invalid product_id. Product does not exist.")
