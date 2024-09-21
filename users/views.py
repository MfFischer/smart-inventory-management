from flask import Blueprint, request, jsonify
from users.models import User
from users.serializers import user_schema
from inventory_system import db
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from marshmallow import ValidationError

users_bp = Blueprint('users', __name__)

# Get all users
@users_bp.route('/', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify(user_schema.dump(users, many=True)), 200

# Create a new user
@users_bp.route('/', methods=['POST'])
def create_user():
    data = request.json
    # Validate and deserialize input
    errors = user_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Create a new User with hashed password
    new_user = User(
        username=data['username'],
        hashed_password=generate_password_hash(data['password']),
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
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(user_schema.dump(user)), 200

# Update a user by ID
@users_bp.route('/<int:user_id>', methods=['PUT'])
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

    if 'hashed_password' in validated_data:
        user.hashed_password = generate_password_hash(
            validated_data['hashed_password']
        )

    db.session.commit()
    return user_schema.jsonify(user), 200

# Delete a user by ID
@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
