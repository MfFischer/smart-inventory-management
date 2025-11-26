from functools import wraps
from flask import jsonify, redirect, url_for, flash, session, render_template
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from modules.users.models import User
from flask_login import current_user, login_required

def get_user():
    """Helper function to get the user from either JWT or session."""
    if 'access_token' in session:
        # If using JWT, verify and get the identity
        verify_jwt_in_request()
        jwt_identity = get_jwt_identity()
        user = User.query.filter_by(username=jwt_identity['username']).first()
    elif current_user.is_authenticated:
        # For session-based authentication, use Flask-Login's current_user
        user = current_user
    else:
        user = None
    return user

def permission_required(permission_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_user()
            if not user:
                return jsonify({'message': 'User not found.'}), 404
            if not user.has_permission(permission_name):
                return jsonify({'message': f'Permission {permission_name} required.'}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

def role_required(*required_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = current_user  # Assuming current_user from Flask-Login is used
            if not user or not user.is_authenticated:
                return redirect(url_for('main.login'))  # Redirect to login if not authenticated

            if user.role not in required_roles:
                flash(f"Access denied: Admin privileges required to access this page.", "error")
                return render_template('access_denied.html')  # Render the custom error page

            return func(*args, **kwargs)
        return wrapper
    return decorator

def active_user_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_user()
        if not user:
            return jsonify({'message': 'User not found.'}), 404
        if user.status != 'active':
            return jsonify({'message': 'User account is not active.'}), 403
        return func(*args, **kwargs)
    return wrapper

def role_or_permission_required(roles=None, permissions=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = get_user()
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
