from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from modules.users.models import User, Permission
from modules.users.serializers import user_schema
from inventory_system import db
from sqlalchemy.exc import IntegrityError
from marshmallow import ValidationError
from functools import wraps

users_bp = Blueprint('users', __name__)

# Utility function to check roles
def role_required(role):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user['username']).first()
            if not user or user.role != role:
                return jsonify({'message': f'Access restricted to {role} role only'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Utility function to check permissions
def permission_required(permission_name):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user['username']).first()
            if not user or not user.has_permission(permission_name):
                return jsonify({'message': f'Permission {permission_name} required.'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# User Registration Endpoint
@users_bp.route('/register', methods=['POST'])
def register():
    data = request.json

    # Validate and deserialize input
    errors = user_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Create a new User with hashed password
    new_user = User(
        username=data['username'],
        hashed_password=User.generate_hash(data['password']),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=data['email'],
        role=data.get('role', 'staff'),
        status=data.get('status', 'active')
    )
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username or email already exists"}), 400

    return jsonify(user_schema.dump(new_user)), 201

# User Login Endpoint
@users_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user or not User.verify_hash(data['password'], user.hashed_password):
        return jsonify({'message': 'Invalid credentials'}), 401

    # Generate access token
    access_token = create_access_token(identity={'username': user.username, 'role': user.role})
    return jsonify({'access_token': access_token}), 200

# Get all users (Admin only)
@users_bp.route('/', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_users():
    users = User.query.all()
    return jsonify(user_schema.dump(users, many=True)), 200

# Create a new user (Admin only)
@users_bp.route('/', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_user():
    data = request.json
    # Validate and deserialize input
    errors = user_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Create a new User with hashed password
    new_user = User(
        username=data['username'],
        hashed_password=User.generate_hash(data['password']),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=data['email'],
        role=data.get('role', 'staff'),
        status=data.get('status', 'active')
    )
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Username or email already exists"}), 400

    return jsonify(user_schema.dump(new_user)), 201

# Get a user by ID
@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(user_schema.dump(user)), 200

# Update a user by ID (Admin only)
@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json

    # Validate and deserialize input
    try:
        validated_data = user_schema.load(data, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    # Update user fields
    if ('username' in validated_data and User.query.filter_by(
            username=validated_data['username']).first()
            and validated_data['username'] != user.username):
        return jsonify({"error": "Username already exists"}), 400

    if ('email' in validated_data and User.query.filter_by(
            email=validated_data['email']).first()
            and validated_data['email'] != user.email):
        return jsonify({"error": "Email already registered"}), 400

    for key, value in validated_data.items():
        setattr(user, key, value)

    if 'password' in validated_data:
        user.hashed_password = User.generate_hash(validated_data['password'])

    db.session.commit()
    return user_schema.jsonify(user), 200

# Delete a user by ID (Admin only)
@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

# Add permission to user (Admin only)
@users_bp.route('/<int:user_id>/permissions', methods=['POST'])
@jwt_required()
@role_required('admin')
def add_permission_to_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    permission_name = data.get('permission')
    permission = Permission.query.filter_by(name=permission_name).first()
    if not permission:
        return jsonify({'message': 'Permission not found'}), 404
    user.add_permission(permission)
    return jsonify({
        'message': f'Permission {permission_name} added to user {user.username}'
    }), 200

# Remove permission from user (Admin only)
@users_bp.route('/<int:user_id>/permissions', methods=['DELETE'])
@jwt_required()
@role_required('admin')
def remove_permission_from_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    permission_name = data.get('permission')
    permission = Permission.query.filter_by(name=permission_name).first()
    if not permission:
        return jsonify({'message': 'Permission not found'}), 404
    user.remove_permission(permission)
    return jsonify({
        'message': f'Permission {permission_name} removed from user {user.username}'
    }), 200

# Get user permissions (Admin only)
@users_bp.route('/<int:user_id>/permissions', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_user_permissions(user_id):
    user = User.query.get_or_404(user_id)
    permissions = [permission.name for permission in user.permissions]
    return jsonify({'permissions': permissions}), 200
