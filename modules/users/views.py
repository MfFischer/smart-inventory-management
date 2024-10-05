from flask import request, jsonify, redirect, url_for, render_template, flash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from modules.users.models import User
from modules.users.serializers import user_schema, login_schema
from inventory_system import db
from sqlalchemy.exc import IntegrityError
from functools import wraps
from flask_restx import Namespace, Resource

# Define a namespace for users-related API operations
api = Namespace('users', description='Users related operations')


# Utility function to check roles before executing an endpoint
def role_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user['username']).first()

            if not user or user.role != role:
                return jsonify({'message': f'Access restricted to {role} role only'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


# Utility function to check if the user has a required permission
def permission_required(permission_name):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user['username']).first()

            if not user or not user.has_permission(permission_name):
                return jsonify({'message': f'Permission {permission_name} required.'}), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator


# Class-based resource for registering a user
@api.route('/register')
class Register(Resource):
    def get(self):
        """Render the registration form."""
        return render_template('register.html')

    def post(self):
        """Handle user registration."""
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = User.generate_hash(password)
        new_user = User(username=username, email=email, hashed_password=hashed_password)

        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('users.login'))


# Class-based resource for user login
@api.route('/login')
class Login(Resource):
    def post(self):
        """User login to generate JWT token."""
        data = request.json
        errors = login_schema.validate(data)
        if errors:
            return jsonify(errors), 422

        user = User.query.filter_by(username=data['username']).first()
        if not user or not User.verify_hash(data['password'], user.hashed_password):
            return jsonify({'message': 'Invalid credentials'}), 401

        access_token = create_access_token(identity={'username': user.username, 'role': user.role})
        return jsonify({'access_token': access_token}), 200


# Class-based resource for getting all users (Admin only)
@api.route('/')
class UsersList(Resource):
    @role_required('admin')
    def get(self):
        """Get all users (Admin only)."""
        users = User.query.all()
        return jsonify(user_schema.dump(users, many=True)), 200

    @role_required('admin')
    def post(self):
        """Create a new user (Admin only)."""
        data = request.json
        errors = user_schema.validate(data)
        if errors:
            return jsonify(errors), 400

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


# Class-based resource for getting, updating, and deleting a user by ID (Admin only)
@api.route('/<int:user_id>')
class UserDetail(Resource):
    @role_required('admin')
    def get(self, user_id):
        """Get a user by ID (Admin only)."""
        user = User.query.get(user_id)
        if user is None:
            return jsonify({'message': 'User not found'}), 404
        return jsonify(user_schema.dump(user)), 200

    @role_required('admin')
    def post(self, user_id):
        """Update a user by ID (Admin only)."""
        user = User.query.get_or_404(user_id)
        username = request.form.get('username')
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        status = request.form.get('status')

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

        try:
            db.session.commit()
            return redirect(url_for('userslist'))
        except IntegrityError:
            db.session.rollback()
            return "Error: Username or Email already exists", 400

    @role_required('admin')
    def delete(self, user_id):
        """Delete a user by ID (Admin only)."""
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return '', 204


# Class-based resource for rendering the user list (HTML view)
@api.route('/users_list')
class UsersListView(Resource):
    def get(self):
        """Render the list of all users."""
        users = User.query.all()
        return render_template('user_list.html', users=users)
