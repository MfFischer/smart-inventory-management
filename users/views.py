from flask import Blueprint, request, jsonify
from users.models import User
from inventory_system import db
from werkzeug.security import generate_password_hash, check_password_hash

users_bp = Blueprint('users', __name__)

# Get all users
@users_bp.route('/', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

# Create a new user
@users_bp.route('/', methods=['POST'])
def create_user():
    data = request.json
    new_user = User(
        username=data.get('username'),
        hashed_password=generate_password_hash(data.get('password')),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        email=data.get('email'),
        role=data.get('role', 'staff'),
        status=data.get('status', 'active')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201

# Get a user by ID
@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200

# Update a user by ID
@users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    if data.get('password'):
        user.hashed_password = generate_password_hash(data.get('password'))
    user.first_name = data.get('first_name', user.first_name)
    user.last_name = data.get('last_name', user.last_name)
    user.email = data.get('email', user.email)
    user.role = data.get('role', user.role)
    user.status = data.get('status', user.status)
    db.session.commit()
    return jsonify(user.to_dict()), 200

# Delete a user by ID
@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
