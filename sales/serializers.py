from marshmallow import Schema, fields, validate, validates, ValidationError
from sales.models import Sale
from products.models import Product

class SaleSchema(Schema):
    id = fields.Int(dump_only=True)
    product_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    total_price = fields.Decimal(required=True, as_string=True)
    sale_status = fields.Str(validate=validate.OneOf(['completed', 'pending']))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('product_id')
    def validate_product_id(self, value):
        # Check if the product exists before creating a sale
        if not Product.query.get(value):
            raise ValidationError("Invalid product_id. Product does not exist.")
