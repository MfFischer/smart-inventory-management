from marshmallow import Schema, fields, validate, validates, ValidationError
from suppliers.models import Supplier


class SupplierSchema(Schema):
    """Schema for validating and serializing Supplier data."""

    # Field definitions with validations
    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, error="Supplier name must not be empty."),
            validate.Length(max=255, error="Supplier name must not exceed 255 characters.")
        ]
    )
    # Required email field, Marshmallow handles email validation
    email = fields.Email(required=True)
    phone = fields.Str(
        validate=validate.Length(max=20)
    )
    # Optional phone field, max length of 20 characters
    address = fields.Str(
        validate=validate.Length(max=500)
    )
    # Optional address field, max length of 500 characters
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('name')
    def validate_name(self, value):
        """Validate that the supplier name is not just whitespace."""
        if not value.strip():
            raise ValidationError("Supplier name must not be empty or contain only whitespace.")

    @validates('email')
    def validate_email(self, value):
        """Validate that the email is unique within the Supplier model."""
        # Check for an existing supplier with the same email address
        if Supplier.query.filter_by(email=value).first():
            raise ValidationError("A supplier with this email already exists.")