from marshmallow import Schema, fields, validate, validates, ValidationError
from products.models import Product


# Schema for serializing and deserializing Product data
class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255)
    )
    # Name is required and should be between 1 and 255 characters
    description = fields.Str(
        validate=validate.Length(max=500)
    )
    # Optional description, maximum length is 500 characters
    price = fields.Decimal(required=True, as_string=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('name')
    def validate_name(self, value):
        """
        Custom validator to ensure the product name is unique.
        """
        if Product.query.filter_by(name=value).first():
            raise ValidationError("A product with this name already exists.")
