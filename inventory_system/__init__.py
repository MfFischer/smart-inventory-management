from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

# Initialize SQLAlchemy and Flask-Migrate instances
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """
    Factory function to create and configure the Flask application.
    """
    # Create Flask app instance
    app = Flask(__name__)

    # Load configuration settings from settings.py
    app.config.from_object('inventory_system.settings')

    # Initialize the database and migration tools with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize JWT Manager
    jwt = JWTManager(app)

    # Import and register blueprints for different modules
    from products.views import products_bp
    from suppliers.views import suppliers_bp
    from inventory.views import inventory_bp
    from sales.views import sales_bp
    from users.views import users_bp

    # Register blueprints with the app
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(sales_bp, url_prefix='/api/sales')
    app.register_blueprint(users_bp, url_prefix='/api/users')

    return app
