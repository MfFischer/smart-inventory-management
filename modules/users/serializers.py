from marshmallow import Schema, fields, validate, validates, ValidationError, pre_dump
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from modules.users.models import User

class UserSchema(Schema):
    """
    Schema for User model with validation rules for fields.
    Includes dynamic fields based on user permissions.
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
    password = fields.Str(required=True, validate=validate.Length(min=6))
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

    @pre_dump(pass_many=False)
    def filter_fields_based_on_permissions(self, data, **kwargs):
        """
        Filters fields based on the current user's permissions.
        """
        verify_jwt_in_request()  # Ensure the request has a valid JWT
        current_user_identity = get_jwt_identity()
        current_user = User.query.filter_by(username=current_user_identity['username']).first()

        # Remove fields based on role or permissions
        if current_user and not current_user.has_permission('view_email'):
            data.email = None  # Remove email if the user doesn't have 'view_email' permission

        # Check for other permissions and adjust data fields accordingly
        if current_user and not current_user.has_permission('view_role'):
            data.role = 'Restricted'  # Hide role details if the user doesn't have 'view_role' permission

        return data

# Create an instance of the schema
user_schema = UserSchema()
