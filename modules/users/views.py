from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from modules.users.models import User
from modules.users.serializers import user_schema, login_schema
from inventory_system import db
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask_restx import Namespace, Resource, fields
from modules.users.decorators import role_required
from marshmallow import ValidationError

# Define JWT authorization scheme for Swagger
authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
    }
}

# Pass the authorizations parameter to Namespace
api = Namespace('users',
                description='Users related operations',
                authorizations=authorizations,
                security='Bearer')

# Define the user model for API documentation (for Swagger)
user_model = api.model('User', {
    'username': fields.String(required=True, description='Username of the user'),
    'email': fields.String(required=True, description='Email of the user'),
    'password': fields.String(required=True, description='User password'),
    'role': fields.String(description='Role of the user (e.g., admin, staff)'),
    'status': fields.String(description='Status of the user (e.g., active, inactive)')
})

# Define a login model specifically for Swagger documentation
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username of the user'),
    'password': fields.String(required=True, description='User password')
})

@api.route('/register')
class Register(Resource):
    @api.expect(user_model)
    @api.doc(responses={201: 'Created',
                        400: 'Validation Error',
                        415: 'Unsupported Media Type',
                        500: 'Internal Server Error'})
    def post(self):
        """Handle user registration (API)."""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        data = request.json
        errors = user_schema.validate(data)
        if errors:
            return errors, 400

        hashed_password = User.generate_hash(data['password'])
        new_user = User(username=data['username'],
                        email=data['email'],
                        hashed_password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return user_schema.dump(new_user), 201  # Directly return the dictionary
        except IntegrityError:
            db.session.rollback()
            return {"error": "Username or email already exists"}, 400
        except SQLAlchemyError as db_err:
            db.session.rollback()
            print(f"Database error: {db_err}")
            return {'message': 'An error occurred while registering the user.'}, 500

@api.route('/login')
class Login(Resource):
    @api.expect(login_model)  # Use the login model here for Swagger
    @api.doc(responses={200: 'Success',
                        400: 'Validation Error',
                        401: 'Unauthorized',
                        500: 'Internal Server Error'})
    def post(self):
        """User login (API)."""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        data = request.json
        errors = login_schema.validate(data)
        if errors:
            return errors, 400  # Return as plain dictionary

        user = User.query.filter_by(username=data['username']).first()
        if not user or not User.verify_hash(data['password'], user.hashed_password):
            return {'message': 'Invalid credentials'}, 401  # Return as plain dictionary

        access_token = create_access_token(identity={
            'username': user.username,
            'role': user.role
        })
        return {'access_token': access_token}, 200  # Return as plain dictionary

@api.route('/')
class UsersList(Resource):
    @api.doc(security='Bearer')
    @jwt_required()
    @role_required('admin')
    @api.doc(responses={200: 'Success', 500: 'Internal Server Error'})
    def get(self):
        """Get all users (Admin only)."""
        try:
            users = User.query.all()
            return user_schema.dump(users, many=True), 200  # Return JSON-serializable dictionary
        except SQLAlchemyError as db_err:
            print(f"Database error: {db_err}")
            return {'message': 'An error occurred while fetching users.'}, 500

    @jwt_required()
    @role_required('admin')
    @api.expect(user_model)
    @api.doc(responses={201: 'Created',
                        400: 'Validation Error',
                        415: 'Unsupported Media Type',
                        500: 'Internal Server Error'})
    def post(self):
        """Create a new user (Admin only)."""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        data = request.json
        errors = user_schema.validate(data)
        if errors:
            return errors, 400

        new_user = User(
            username=data['username'],
            hashed_password=User.generate_hash(data['password']),
            email=data['email'],
            role=data.get('role', 'staff'),
            status=data.get('status', 'active')
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            return user_schema.dump(new_user), 201
        except IntegrityError:
            db.session.rollback()
            return {"error": "Username or email already exists"}, 400
        except SQLAlchemyError as db_err:
            db.session.rollback()
            print(f"Database error: {db_err}")
            return {'message': 'An error occurred while creating the user.'}, 500

@api.route('/<int:user_id>')
class UserDetail(Resource):
    @api.doc(security='Bearer')
    @jwt_required()
    @role_required('admin')
    def get(self, user_id):
        """Get a user by ID (Admin only)."""
        try:
            user = User.query.get_or_404(user_id)
            return user_schema.dump(user), 200
        except SQLAlchemyError as db_err:
            print(f"Database error: {db_err}")
            return {'message': 'An error occurred while fetching the user.'}, 500

    @jwt_required()
    @role_required('admin')
    @api.expect(user_model)
    @api.doc(responses={200: 'Success',
                        400: 'Validation Error',
                        404: 'Not Found',
                        415: 'Unsupported Media Type',
                        500: 'Internal Server Error'})
    def put(self, user_id):
        """Update a user by ID (Admin only)."""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        user = User.query.get_or_404(user_id)
        data = request.json
        errors = user_schema.validate(data, partial=True)
        if errors:
            return errors, 400

        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.role = data.get('role', user.role)
        user.status = data.get('status', user.status)

        try:
            db.session.commit()
            return user_schema.dump(user), 200
        except SQLAlchemyError as db_err:
            db.session.rollback()
            print(f"Database error: {db_err}")
            return {'message': 'An error occurred while updating the user.'}, 500

    @jwt_required()
    @role_required('admin')
    @api.doc(responses={204: 'No Content', 404: 'Not Found', 500: 'Internal Server Error'})
    def delete(self, user_id):
        """Delete a user by ID (Admin only)."""
        user = User.query.get_or_404(user_id)
        try:
            db.session.delete(user)
            db.session.commit()
            return '', 204
        except SQLAlchemyError as db_err:
            db.session.rollback()
            print(f"Database error: {db_err}")
            return {'message': 'An error occurred while deleting the user.'}, 500
