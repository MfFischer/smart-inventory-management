from marshmallow import Schema, fields, post_dump
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    first_name = fields.Str()
    last_name = fields.Str()
    role = fields.Str()
    status = fields.Str()

    @post_dump(pass_many=True)
    def filter_fields_based_on_permissions(self, data, many, **kwargs):
        try:
            # Only verify JWT if explicitly required; set to optional to avoid error if not present
            verify_jwt_in_request(optional=True)
            current_user = get_jwt_identity()

            # Apply filtering based on user role or other conditions
            if current_user and current_user.get('role') != 'admin':
                for item in (data if many else [data]):
                    item.pop('email', None)

        except NoAuthorizationError:
            # If no JWT is present, skip filtering based on authorization
            pass

        return data

# Instance of the schema
user_schema = UserSchema()

# Define a schema specifically for login data (username and password)
class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

# Instance of the schema for login data
login_schema = LoginSchema()