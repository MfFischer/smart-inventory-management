from marshmallow import Schema, fields, validate, validates, ValidationError
from permissions.models import Permission


class PermissionSchema(Schema):
    """
    Schema for serializing and deserializing Permission objects.
    """
    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=100)
    )
    description = fields.Str(validate=validate.Length(max=255))

    @validates('name')
    def validate_name(self, value):
        """
        Validates that the permission name is unique.
        """
        if Permission.query.filter_by(name=value).first():
            raise ValidationError("Permission name already exists.")


# Create an instance of the schema for single and multiple objects
permission_schema = PermissionSchema()
permissions_schema = PermissionSchema(many=True)

