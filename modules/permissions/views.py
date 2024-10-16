from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from modules.permissions.models import Permission, db
from modules.permissions.serializers import permission_schema, permissions_schema
from modules.users.decorators import role_required
from marshmallow import ValidationError


# Create a Blueprint for the permissions module with a URL prefix
permissions_bp = Blueprint('permissions', __name__,
                           url_prefix='/api/permissions')

@permissions_bp.route('/', methods=['POST'])
@jwt_required()
# Restrict permission creation to admin users
@role_required('admin')
def create_permission():
    """
    Create a new permission.
    """
    data = request.json
    try:
        # Validate and deserialize input data for permission creation
        validated_data = permission_schema.load(data)
    except ValidationError as err:
        # Return validation errors if input data is invalid
        return jsonify(err.messages), 400

    # Create a new Permission instance with validated data
    new_permission = Permission(
        name=validated_data['name'],
        description=validated_data.get('description')
    )

    try:
        # Add and commit the new permission to the database
        db.session.add(new_permission)
        db.session.commit()
    except IntegrityError:
        # Rollback the transaction if permission name already exists
        db.session.rollback()
        return jsonify({"error": "Permission name already exists"}), 400

    # Return the created permission with a 201 status code
    return jsonify(permission_schema.dump(new_permission)), 201

@permissions_bp.route('/', methods=['GET'])
@jwt_required()
# Restrict permission listing to admin users
@role_required('admin')
def get_permissions():
    """
    Retrieve a list of all permissions.
    """
    # Query all permissions from the database
    permissions = Permission.query.all()
    # Return the list of permissions in serialized form
    return jsonify(permissions_schema.dump(permissions)), 200

@permissions_bp.route('/<int:permission_id>',
                      methods=['GET'])
@jwt_required()
# Restrict viewing specific permission to admin users
@role_required('admin')
def get_permission(permission_id):
    """
    Retrieve a specific permission by ID.
    """
    # Query the permission by its ID
    permission = Permission.query.get(permission_id)
    if not permission:
        # Return a 404 if the permission is not found
        return jsonify({"message": "Permission not found"}), 404

    # Return the serialized permission data
    return jsonify(permission_schema.dump(permission)), 200

@permissions_bp.route('/<int:permission_id>',
                      methods=['PUT'])
@jwt_required()
# Restrict permission updates to admin users
@role_required('admin')
def update_permission(permission_id):
    """
    Update an existing permission.
    """
    # Query the permission by its ID
    permission = Permission.query.get(permission_id)
    if not permission:
        # Return a 404 if the permission is not found
        return jsonify({"message": "Permission not found"}), 404

    data = request.json
    try:
        # Validate and deserialize input data for partial updates
        validated_data = permission_schema.load(data, partial=True)
    except ValidationError as err:
        # Return validation errors if input data is invalid
        return jsonify(err.messages), 400

    # Update the permission fields with validated data
    for key, value in validated_data.items():
        setattr(permission, key, value)

    # Commit the updated permission to the database
    db.session.commit()
    # Return the updated permission data
    return jsonify(permission_schema.dump(permission)), 200

@permissions_bp.route('/<int:permission_id>',
                      methods=['DELETE'])
@jwt_required()
# Restrict permission deletion to admin users
@role_required('admin')
def delete_permission(permission_id):
    """
    Delete a specific permission.
    """
    # Query the permission by its ID
    permission = Permission.query.get(permission_id)
    if not permission:
        # Return a 404 if the permission is not found
        return jsonify({"message": "Permission not found"}), 404

    # Delete the permission from the database
    db.session.delete(permission)
    db.session.commit()
    # Return a 204 status code indicating successful deletion
    return '', 204
