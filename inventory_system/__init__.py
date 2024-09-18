from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    # Load the configuration
    app.config.from_object('inventory_system.settings')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register the suppliers blueprint
    from suppliers.urls import suppliers_bp
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')

    return app
