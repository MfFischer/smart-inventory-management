from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app
from flask_jwt_extended import unset_jwt_cookies
from modules.users.models import User
from flask_login import login_user, logout_user, login_required, current_user
from modules.permissions.models import  db
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import logging
from modules.demo.demo_helpers import init_demo_session, is_demo_mode, clear_demo_session, get_demo_user
from modules.demo.demo_user import DemoUser

main_bp = Blueprint('main', __name__)

# Set up logging
logger = logging.getLogger(__name__)

@main_bp.route('/')
def home():
    """Root route - show landing page if not authenticated, dashboard if authenticated"""
    if current_user.is_authenticated:
        # Check if user has a role that can access dashboard
        if current_user.role in ['admin', 'staff', 'owner']:
            return redirect(url_for('users.personal_dashboard'))
    # Otherwise show the landing page
    return render_template('landing.html')


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        # Check if user has a role that can access dashboard
        if current_user.role in ['admin', 'staff', 'owner']:
            # Redirect to appropriate dashboard based on role
            return redirect(url_for('users.personal_dashboard'))

    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter_by(username=username).first()
            logger.info(f"User retrieved: {user}")

            if user and User.verify_hash(password, user.hashed_password):
                login_user(user)

                # Update last login in a new session to avoid locks
                try:
                    user.last_login = datetime.now()
                    db.session.commit()
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"Error updating last login: {str(e)}")
                    # Continue with login even if last_login update fails

                # Set session data
                session['logged_in'] = True
                session['user_id'] = user.id
                session['role'] = user.role
                logger.info(f"Session data set: {session['logged_in']} {session['user_id']} {session['role']}")

                flash('Welcome back!', 'success')
                return redirect(url_for('users.personal_dashboard'))
            else:
                flash('Invalid username or password', 'error')
                logger.info("Login failed, redirecting back to login page")
                return render_template('login.html')

        except Exception as e:
            db.session.rollback()
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')
            return render_template('login.html')

    return render_template('login.html')


@main_bp.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        session.clear()
        response = redirect(url_for('main.login'))
        unset_jwt_cookies(response)
        flash("You have been logged out.", "success")
        return response
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        flash("An error occurred during logout.", "error")
        return redirect(url_for('main.index'))


@main_bp.route('/profile')
@login_required
def profile():
    try:
        return render_template('profile.html', user=current_user)
    except Exception as e:
        logger.error(f"Profile page error: {str(e)}")
        flash("An error occurred while loading the profile page.", "error")
        return redirect(url_for('main.index'))


@main_bp.route('/landing')
def landing():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        # Check if user has a role that can access dashboard
        if current_user.role in ['admin', 'staff', 'owner']:
            # Redirect to appropriate dashboard based on role
            return redirect(url_for('users.personal_dashboard'))
    # Otherwise show the landing page
    return render_template('landing.html')


@main_bp.route('/')
def home():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        # Check if user has a role that can access dashboard
        if current_user.role in ['admin', 'staff', 'owner']:
            # Redirect to appropriate dashboard based on role
            return redirect(url_for('users.personal_dashboard'))
    # Otherwise show the landing page
    return render_template('landing.html')


@main_bp.route('/index')
def index():
    """Deprecated: Redirect to dashboard if authenticated, otherwise to login"""
    if current_user.is_authenticated:
        return redirect(url_for('users.personal_dashboard'))
    return redirect(url_for('main.login'))


@main_bp.route('/demo')
def start_demo():
    """Start a demo session without login"""
    try:
        # Clear any existing session
        session.clear()

        # Initialize demo session with sample data
        init_demo_session()

        # Create demo user and log them in
        demo_user = get_demo_user()
        if demo_user:
            login_user(demo_user, remember=False)
            flash('Welcome to Demo Mode! Explore all features - your data will not be saved.', 'info')
            return redirect(url_for('users.personal_dashboard'))
        else:
            flash('Failed to start demo mode. Please try again.', 'error')
            return redirect(url_for('main.landing'))

    except Exception as e:
        logger.error(f"Demo mode error: {str(e)}")
        flash('An error occurred starting demo mode.', 'error')
        return redirect(url_for('main.landing'))


@main_bp.route('/exit-demo')
def exit_demo():
    """Exit demo mode and return to landing page"""
    try:
        if is_demo_mode():
            clear_demo_session()
            logout_user()
            flash('You have exited demo mode. Sign up to save your data!', 'success')
        return redirect(url_for('main.landing'))
    except Exception as e:
        logger.error(f"Exit demo error: {str(e)}")
        return redirect(url_for('main.landing'))


# Error handlers
@main_bp.errorhandler(404)
def not_found_error():
    return render_template('errors/404.html'), 404


@main_bp.errorhandler(500)
def internal_error():
    db.session.rollback()
    return render_template('errors/500.html'), 500


# Add this to handle database connection issues
@main_bp.errorhandler(SQLAlchemyError)
def handle_db_error(error):
    db.session.rollback()
    logger.error(f"Database error: {str(error)}")
    flash("A database error occurred. Please try again.", "error")
    return redirect(url_for('main.index'))