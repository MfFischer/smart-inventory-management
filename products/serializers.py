from marshmallow import Schema, fields, validate, validates, ValidationError
from products.models import Product


class ProductSchema(Schema):
    """Schema for validating and serializing Product data."""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str()
    price = fields.Decimal(as_string=True, required=True)
    quantity_in_stock = fields.Int(required=True)
    reorder_point = fields.Int(required=True)
    reorder_quantity = fields.Int(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('name')
    def validate_name(self, value):
        """Validate that the product name is unique."""
        if Product.query.filter_by(name=value).first():
            raise ValidationError("A product with this name already exists.")

