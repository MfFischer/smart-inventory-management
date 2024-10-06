from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from modules.users.models import User
from modules.users.serializers import user_schema, login_schema
from inventory_system import db
from sqlalchemy.exc import IntegrityError
from flask_restx import Namespace, Resource
from modules.users.decorators import role_required  # Ensure role_required is imported correctly

# Define a namespace for users-related API operations
api = Namespace('users', description='Users related operations')

@api.route('/register')
class Register(Resource):
    def post(self):
        """Handle user registration (API)."""
        data = request.json
        errors = user_schema.validate(data)
        if errors:
            return jsonify(errors), 400

        hashed_password = User.generate_hash(data['password'])
        new_user = User(username=data['username'], email=data['email'], hashed_password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return jsonify(user_schema.dump(new_user)), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "Username or email already exists"}), 400

@api.route('/login')
class Login(Resource):
    def post(self):
        """User login (API)."""
        data = request.json
        errors = login_schema.validate(data)
        if errors:
            return jsonify(errors), 400

        user = User.query.filter_by(username=data['username']).first()
        if not user or not User.verify_hash(data['password'], user.hashed_password):
            return jsonify({'message': 'Invalid credentials'}), 401

        # Generate access token with user information
        access_token = create_access_token(identity={'username': user.username, 'role': user.role})
        return jsonify({'access_token': access_token}), 200

@api.route('/')
class UsersList(Resource):
    @jwt_required()  # Ensure user is logged in
    @role_required('admin')  # Check if the user has 'admin' role
    def get(self):
        """Get all users (Admin only)."""
        users = User.query.all()
        return jsonify(user_schema.dump(users, many=True)), 200

    @jwt_required()  # Ensure user is logged in
    @role_required('admin')  # Check if the user has 'admin' role
    def post(self):
        """Create a new user (Admin only)."""
        data = request.json
        errors = user_schema.validate(data)
        if errors:
            return jsonify(errors), 400

        new_user = User(
            username=data['username'],
            hashed_password=User.generate_hash(data['password']),
            email=data['email'],
            role=data.get('role', 'staff'),  # Default role is 'staff'
            status=data.get('status', 'active')  # Default status is 'active'
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            return jsonify(user_schema.dump(new_user)), 201
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "Username or email already exists"}), 400

@api.route('/<int:user_id>')
class UserDetail(Resource):
    @jwt_required()  # Ensure user is logged in
    @role_required('admin')  # Check if the user has 'admin' role
    def get(self, user_id):
        """Get a user by ID (Admin only)."""
        user = User.query.get_or_404(user_id)
        return jsonify(user_schema.dump(user)), 200

    #@jwt_required()  # Ensure user is logged in
    @role_required('admin')  # Check if the user has 'admin' role
    def put(self, user_id):
        """Update a user by ID (Admin only)."""
        user = User.query.get_or_404(user_id)
        data = request.json
        errors = user_schema.validate(data, partial=True)
        if errors:
            return jsonify(errors), 400

        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.role = data.get('role', user.role)
        user.status = data.get('status', user.status)

        db.session.commit()
        return jsonify(user_schema.dump(user)), 200

    #@jwt_required()  # Ensure user is logged in
    @role_required('admin')  # Check if the user has 'admin' role
    def delete(self, user_id):
        """Delete a user by ID (Admin only)."""
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return '', 204
