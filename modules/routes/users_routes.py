from flask import Blueprint, render_template, request, redirect, url_for, flash
from inventory_system import db
from modules.users.models import User
from flask_jwt_extended import jwt_required, create_access_token
from sqlalchemy.exc import IntegrityError
from modules.users.decorators import role_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/register', methods=['GET', 'POST'])
def user_register():
    """Render the registration form and handle user registration."""
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists. Please choose a different one.', 'error')
            return render_template('register.html')

        hashed_password = User.generate_hash(password)
        new_user = User(username=username, email=email, hashed_password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('users.user_login'))

    return render_template('register.html')

@users_bp.route('/login', methods=['GET', 'POST'])
def user_login():
    """Render the login form and handle user login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and User.verify_hash(password, user.hashed_password):
            access_token = create_access_token(identity={'username': user.username, 'role': user.role})
            flash('Login successful!', 'success')
            # Redirect to users list view with the token in a cookie or stored in local storage
            response = redirect(url_for('users.users_list_view'))
            # Set the token as a cookie
            response.set_cookie('access_token', access_token)  # Set the token as a cookie
            return response
        else:
            flash('Invalid credentials', 'error')

    return render_template('login.html')


@users_bp.route('/users_list')
#@jwt_required()
#@role_required('admin')
def users_list_view():
    """Render the list of users (Admin only)."""
    users = User.query.all()
    return render_template('user_list.html', users=users)

@users_bp.route('/create', methods=['GET', 'POST'])
#@jwt_required()
#@role_required('admin')
def user_create():
    """Admin-only route for creating a new user."""
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            role = request.form.get('role', 'staff')
            status = request.form.get('status', 'active')

            hashed_password = User.generate_hash(password)
            new_user = User(username=username, email=email, hashed_password=hashed_password, role=role, status=status)

            db.session.add(new_user)
            db.session.commit()

            flash('User created successfully!', 'success')
            return redirect(url_for('users.users_list_view'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Username or Email already exists', 'error')

    return render_template('create_user.html')

@users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
#@jwt_required()
#@role_required('admin')
def user_edit(user_id):
    """Render the form to edit a user."""
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.role = request.form.get('role')
        user.status = request.form.get('status')

        try:
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('users.users_list_view'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Username or Email already exists', 'error')

    return render_template('edit_user.html', user=user)

@users_bp.route('/delete/<int:user_id>', methods=['POST'])
#@jwt_required()
#@role_required('admin')
def user_delete(user_id):
    """Delete a user (Admin only)."""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('users.users_list_view'))
