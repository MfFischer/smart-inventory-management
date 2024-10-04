from flask import Blueprint, request, jsonify,  redirect, url_for
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from modules.users.models import User
from modules.users.serializers import user_schema, login_schema
from inventory_system import db
from sqlalchemy.exc import IntegrityError
from functools import wraps

users_bp = Blueprint('users', __name__)


# Utility function to check roles before executing an endpoint
def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Retrieve current user identity from JWT
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user['username']).first()

            # If user doesn't exist or doesn't have the required role, return a 403 error
            if not user or user.role != role:
                return jsonify({'message': f'Access restricted to {role} role only'}), 403

            # Proceed to the original function
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# Utility function to check if the user has a required permission
def permission_required(permission_name):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Retrieve current user identity from JWT
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user['username']).first()

            # Check if user has the required permission
            if not user or not user.has_permission(permission_name):
                return jsonify({'message': f'Permission {permission_name} required.'}), 403

            # Proceed to the original function
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# User registration endpoint
@users_bp.route('/register', methods=['POST'])
def register():
    # Get JSON data from the request
    data = request.json
    # Validate and deserialize the input data
    errors = user_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Create a new user with hashed password and optional fields
    new_user = User(
        username=data['username'],
        hashed_password=User.generate_hash(data['password']),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=data['email'],
        # Default role is 'staff'
        role=data.get('role', 'staff'),
        # Default status is 'active'
        status=data.get('status', 'active')
    )

    # Try adding the new user to the database
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        # Roll back if a username or email already exists
        db.session.rollback()
        return jsonify({"error": "Username or email already exists"}), 400
    # Return the created user
    return jsonify(user_schema.dump(new_user)), 201


# User login endpoint
@users_bp.route('/login', methods=['POST'])
def login():
    # Get JSON data from the request
    data = request.json

    # Validate input using LoginSchema
    errors = login_schema.validate(data)
    if errors:
        # Return validation errors if any
        return jsonify(errors), 422

    user = User.query.filter_by(username=data['username']).first()

    # Verify if the user exists and the password is correct
    if not user or not User.verify_hash(data['password'], user.hashed_password):
        return jsonify({'message': 'Invalid credentials'}), 401

    # Create an access token for the user
    access_token = create_access_token(
        identity={
        'username': user.username,
        'role': user.role}
    )
    return jsonify({'access_token': access_token}), 200


# Get all users (Admin only)
@users_bp.route('/', methods=['GET'])
def get_users():
    # Fetch all users from the database
    users = User.query.all()
    # Return all users
    return jsonify(user_schema.dump(users, many=True)), 200


# Create a new user (Admin only)
@users_bp.route('/', methods=['POST'])
def create_user():
    data = request.json

    # Validate and deserialize the input data
    errors = user_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Create a new user with hashed password and optional fields
    new_user = User(
        username=data['username'],
        hashed_password=User.generate_hash(data['password']),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=data['email'],
        role=data.get('role', 'staff'),
        status=data.get('status', 'active')  #
    )

    # Try adding the new user to the database
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        # Roll back if a username or email already exists
        db.session.rollback()
        return jsonify({"error": "Username or email already exists"}), 400

    return jsonify(user_schema.dump(new_user)), 201


# Get a user by ID
@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Fetch user by ID
    user = User.query.get(user_id)
    if user is None:
        # Return error if not found
        return jsonify({'message': 'User not found'}), 404
    # Return the found user
    return jsonify(user_schema.dump(user)), 200


# Update a user by ID (Admin only)
@users_bp.route('/<int:user_id>', methods=['POST'])
def update_user(user_id):
    # Find user by ID, return 404 if not found
    user = User.query.get_or_404(user_id)

    # Get form data
    username = request.form.get('username')
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    role = request.form.get('role')
    status = request.form.get('status')

    # Update user fields if data is provided
    if username:
        user.username = username
    if email:
        user.email = email
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    if role:
        user.role = role
    if status:
        user.status = status

    # Commit the changes to the database
    try:
        db.session.commit()
        # Redirect to user list
        return redirect(url_for('users.view_users'))
    except IntegrityError:
        # Roll back if there's a conflict
        db.session.rollback()
        return "Error: Username or Email already exists", 400


# Delete a user by ID (Admin only)
@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Find user by ID, return 404 if not found
    user = User.query.get_or_404(user_id)
    # Delete the user
    db.session.delete(user)
    # Commit the changes
    db.session.commit()
    return '', 204
