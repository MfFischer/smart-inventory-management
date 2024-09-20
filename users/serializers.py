from marshmallow import Schema, fields, validate, validates, ValidationError
from users.models import User

class UserSchema(Schema):
    """
    Schema for User model with validation rules for fields.
    """
    id = fields.Int(dump_only=True)
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=100)
    )
    email = fields.Email(required=True)
    first_name = fields.Str(validate=validate.Length(max=255))
    last_name = fields.Str(validate=validate.Length(max=255))
    role = fields.Str(
        validate=validate.OneOf(['admin', 'staff'])
    )
    status = fields.Str(
        validate=validate.OneOf(['active', 'inactive'])
    )
    last_login = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('username')
    def validate_username(self, value):
        """
        Validates that the username is unique.

        Raises:
            ValidationError: If the username already exists in the database.
        """
        if User.query.filter_by(username=value).first():
            raise ValidationError("Username already exists.")
