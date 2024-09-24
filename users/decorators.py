from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from users.models import User

def permission_required(permission_name):
    """
    Decorator to check if a user has the specified permission.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user['username']).first()
            if not user:
                return jsonify({'message': 'User not found.'}), 404
            if not user.has_permission(permission_name):
                return jsonify({'message': f'Permission {permission_name} required.'}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

def role_required(*required_roles):
    """
    Decorator to check if a user has any of the required roles.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user['username']).first()
            if not user:
                return jsonify({'message': 'User not found.'}), 404
            if user.role not in required_roles:
                return jsonify({'message': f'Access forbidden: {required_roles} role required.'}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

def active_user_required(func):
    """
    Decorator to check if a user is active.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user['username']).first()
        if not user:
            return jsonify({'message': 'User not found.'}), 404
        if user.status != 'active':
            return jsonify({'message': 'User account is not active.'}), 403
        return func(*args, **kwargs)
    return wrapper

def role_or_permission_required(roles=None, permissions=None):
    """
    Decorator to check if a user has any of the specified roles or permissions.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user = get_jwt_identity()
            user = User.query.filter_by(username=current_user['username']).first()
            if not user:
                return jsonify({'message': 'User not found.'}), 404

            # Check if user has any of the required roles
            if roles and user.role in roles:
                return func(*args, **kwargs)

            # Check if user has any of the required permissions
            if permissions and any(user.has_permission(perm) for perm in permissions):
                return func(*args, **kwargs)

            return jsonify({'message': 'Access forbidden: insufficient role or permission.'}), 403
        return wrapper
    return decorator
