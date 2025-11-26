from flask import Flask, render_template, Blueprint, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_restx import Api
from flask_login import LoginManager, login_required, login_user, current_user, logout_user
from flask_mail import Mail
from flask_apscheduler import APScheduler
import os
from .swagger import init_swagger
from logging.handlers import RotatingFileHandler
import logging
from modules.utils.email_automation import email_automation

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()
mail = Mail()
scheduler = APScheduler()

# Define the authorization method for Swagger globally
authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
    }
}


def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, '../app/templates')
    app = Flask(__name__, template_folder=template_dir, static_folder='../app/static')
    app.config['DEBUG'] = True


    # Enable automatic reloading of templates
    app.config['TEMPLATES_AUTO_RELOAD'] = True


    app.config.from_object('inventory_system.settings')

    # Setup file logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/inventory_system.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.info('Inventory System startup')

    # Email configuration
    app.config.update({
        'MAIL_SERVER': 'smtp.gmail.com',
        'MAIL_PORT': 465,
        'MAIL_USE_SSL': True,
        'MAIL_USERNAME': os.getenv('GMAIL_USER'),
        'MAIL_PASSWORD': os.getenv('GMAIL_APP_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.getenv('GMAIL_USER'),
        #SITE_URL': os.getenv('SITE_URL', 'https://bmsgo.online/')
    })

    # APScheduler configuration
    app.config.update({
        'SCHEDULER_API_ENABLED': True,
        'SCHEDULER_TIMEZONE': 'UTC'
    })

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory_system.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'timeout': 15,
            'check_same_thread': False
        }
    }

    # Print email configuration (remove in production)
    app.logger.info("Mail Username: %s", app.config.get('MAIL_USERNAME'))
    app.logger.info("Mail Password Set: %s", bool(app.config.get('MAIL_PASSWORD')))
    app.logger.info("Mail Server: %s", app.config.get('MAIL_SERVER'))
    app.logger.info("Mail Port: %s", app.config.get('MAIL_PORT'))

    # Initialize extensions with app context
    db.init_app(app)

    with app.app_context():
        # Import all models here to ensure they're registered with SQLAlchemy
        from modules.users.models import User
        from modules.permissions.models import Permission, user_permissions
        from modules.products.models import Product
        from modules.inventory.models import Inventory
        from modules.sales.models import Sale
        from modules.suppliers.models import Supplier, AccountsPayable
        from modules.accounts_receivable.models import AccountsReceivable
        from modules.expenses.models import Expense
        from modules.ReturnedDamagedItem.models import ReturnedDamagedItem
        from modules.announcements.models import Announcement
        from modules.business.models import Business

        # Initialize migrations after all models are imported
        migrate.init_app(app, db)

    # Initialize other extensions
    jwt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"
    mail.init_app(app)
    scheduler.init_app(app)

    # Initialize email automation
    email_automation.init_app(app)

    # Start schedulers
    scheduler.start()

    @login_manager.user_loader
    def load_user(user_id):
        from modules.users.models import User
        from modules.demo.demo_helpers import is_demo_mode, get_demo_user

        # Check if this is a demo session
        if is_demo_mode() and user_id == 'demo':
            return get_demo_user()

        # Otherwise load real user from database
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    # Scheduler tasks for email automation
    @scheduler.task('cron', id='check_trial_reminders', hour=9)
    def scheduled_trial_reminders():
        with app.app_context():
            email_automation.check_trial_reminders()

    @scheduler.task('cron', id='check_low_inventory', hour=10)
    def scheduled_inventory_check():
        with app.app_context():
            email_automation.check_low_inventory()

    # Root route
    @app.route('/')
    def redirect_to_landing():
        return redirect(url_for('main.landing'))

    # API Blueprint setup
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    api = Api(api_bp,
              title="Smart Inventory System API",
              version="1.0",
              description="API for managing inventory, products, sales, users, and reports."
              )

    # Register API namespaces
    from modules.products.views import api as products_ns
    from modules.suppliers.views import api as suppliers_ns
    from modules.inventory.views import api as inventory_ns
    from modules.sales.views import api as sales_ns
    from modules.users.views import api as users_ns
    from modules.ReturnedDamagedItem.views import api as returned_damaged_ns
    from modules.accounts_receivable.views import api as accounts_receivable_ns
    from modules.expenses.views import api as expenses_ns

    api.add_namespace(products_ns, path='/products')
    api.add_namespace(suppliers_ns, path='/suppliers')
    api.add_namespace(inventory_ns, path='/inventory')
    api.add_namespace(sales_ns, path='/sales')
    api.add_namespace(users_ns, path='/users')
    api.add_namespace(returned_damaged_ns, path='/returns')
    api.add_namespace(accounts_receivable_ns, path='/accounts_receivable')
    api.add_namespace(expenses_ns, path='/expenses')

    app.register_blueprint(api_bp)

    # Register HTML route blueprints
    from .routes import main_bp
    from modules.routes.products_routes import products_bp
    from modules.routes.sales_routes import sales_bp
    from modules.routes.inventory_routes import inventory_bp
    from modules.routes.users_routes import users_bp
    from modules.routes.suppliers_routes import suppliers_bp
    from modules.routes.returns_routes import returns_bp
    from modules.routes.accounts_receivable_routes import accounts_receivable_bp
    from modules.routes.expenses_routes import expenses_bp
    from modules.routes.permission_routes import permissions_bp
    from modules.routes.tables_reports_routes import tables_reports_bp
    from modules.routes.visualizations_routes import visualizations_bp
    from modules.routes.announcement_routes import announcements_bp
    from modules.routes.business_routes import business_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(returns_bp, url_prefix='/returns')
    app.register_blueprint(accounts_receivable_bp, url_prefix='/accounts_receivable')
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(permissions_bp, url_prefix='/permissions')
    app.register_blueprint(tables_reports_bp, url_prefix='/tables_reports')
    app.register_blueprint(visualizations_bp, url_prefix='/visualizations')
    app.register_blueprint(announcements_bp, url_prefix='/announcements')
    app.register_blueprint(business_bp, url_prefix='/business')

    # Initialize Swagger
    init_swagger(app)

    # JWT token middleware
    @app.before_request
    def auto_include_token():
        if 'access_token' in session and request.endpoint not in ('main.login', 'main.logout', 'static'):
            request.headers['Authorization'] = f"Bearer {session['access_token']}"

    return app