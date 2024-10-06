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

    @pre_dump(pass_many=True)
    def filter_fields_based_on_permissions(self, data, many):
        """
        Filters fields based on the current user's permissions.
        Supports filtering for single or multiple objects.
        """
        verify_jwt_in_request()
        current_user_identity = get_jwt_identity()
        current_user = User.query.filter_by(username=current_user_identity['username']).first()

        if many:
            # If we're dealing with multiple users (a list), iterate over each user
            for user in data:
                self._apply_permission_filters(user, current_user)
        else:
            # For a single user
            self._apply_permission_filters(data, current_user)

        return data

    def _apply_permission_filters(self, user_data, current_user):
        """
        Helper function to apply permission filters to a single user.
        """
        if current_user and not current_user.has_permission('view_email'):
            user_data.email = None

        if current_user and not current_user.has_permission('view_role'):
            user_data.role = 'Restricted'

# Create an instance of the schema
user_schema = UserSchema()

class LoginSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=6))

login_schema = LoginSchema()

