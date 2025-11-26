from marshmallow import Schema, fields, validate, validates, ValidationError
from modules.suppliers.models import Supplier


class SupplierSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    contact = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    phone = fields.Str(allow_none=True)
    email = fields.Email(required=True)
    address = fields.Str(allow_none=True)

    @validates('name')
    def validate_name(self, value):
        """Validate that the supplier name is not just whitespace."""
        if not value.strip():
            raise ValidationError("Supplier name must not be empty or contain only whitespace.")

    @validates('email')
    def validate_email(self, value, **kwargs):
        """Validate that the email is unique within the Supplier model."""
        # Get the supplier being updated (if any)
        supplier_id = self.context.get('supplier_id')

        existing_supplier = Supplier.query.filter_by(email=value).first()

        # If a supplier with this email exists and it's not the one being updated
        if existing_supplier and (not supplier_id or existing_supplier.id != supplier_id):
            raise ValidationError("A supplier with this email already exists.")