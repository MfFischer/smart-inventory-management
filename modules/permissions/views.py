from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from modules.permissions.models import Permission, db
from modules.permissions.serializers import permission_schema, permissions_schema
from modules.users.decorators import role_required
from marshmallow import ValidationError



# Create a Blueprint for the permissions module
permissions_bp = Blueprint('permissions', __name__, url_prefix='/api/permissions')

@permissions_bp.route('/', methods=['POST'])
@jwt_required()
# Only admin can create permissions
@role_required('admin')
def create_permission():
    """
    Create a new permission.
    """
    data = request.json
    try:
        # Validate and deserialize input
        validated_data = permission_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    # Create a new Permission instance
    new_permission = Permission(
        name=validated_data['name'],
        description=validated_data.get('description')
    )

    try:
        db.session.add(new_permission)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Permission name already exists"}), 400

    return jsonify(permission_schema.dump(new_permission)), 201

@permissions_bp.route('/', methods=['GET'])
@jwt_required()
# Only admin can view all permissions
@role_required('admin')
def get_permissions():
    """
    Retrieve a list of all permissions.
    """
    permissions = Permission.query.all()
    return jsonify(permissions_schema.dump(permissions)), 200

@permissions_bp.route('/<int:permission_id>', methods=['GET'])
@jwt_required()
# Only admin can view a specific permission
@role_required('admin')
def get_permission(permission_id):
    """
    Retrieve a specific permission by ID.
    """
    permission = Permission.query.get(permission_id)
    if not permission:
        return jsonify({"message": "Permission not found"}), 404

    return jsonify(permission_schema.dump(permission)), 200

@permissions_bp.route('/<int:permission_id>', methods=['PUT'])
@jwt_required()
# Only admin can update permissions
@role_required('admin')
def update_permission(permission_id):
    """
    Update an existing permission.
    """
    permission = Permission.query.get(permission_id)
    if not permission:
        return jsonify({"message": "Permission not found"}), 404

    data = request.json
    try:
        # Validate and deserialize input with partial updates
        validated_data = permission_schema.load(data, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    # Update fields
    for key, value in validated_data.items():
        setattr(permission, key, value)

    db.session.commit()
    return jsonify(permission_schema.dump(permission)), 200

@permissions_bp.route('/<int:permission_id>', methods=['DELETE'])
@jwt_required()
# Only admin can delete permissions
@role_required('admin')
def delete_permission(permission_id):
    """
    Delete a specific permission.
    """
    permission = Permission.query.get(permission_id)
    if not permission:
        return jsonify({"message": "Permission not found"}), 404

    db.session.delete(permission)
    db.session.commit()
    return '', 204

