from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object('inventory_system.settings')

    db.init_app(app)
    migrate.init_app(app, db)

    from modules.suppliers.views import suppliers_bp
    app.register_blueprint(suppliers_bp, url_prefix='/api')

    from modules.inventory.views import inventory_bp
    app.register_blueprint(inventory_bp, url_prefix='/api')

    return app
