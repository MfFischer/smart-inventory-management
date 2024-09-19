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

    #Import models
    from suppliers.models import Supplier
    from inventory.models import Inventory
    from products.models import Product
    from sales.models import Sale
    from users.models import User

    # Register Blueprints
    from suppliers.views import suppliers_bp
    app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')

    return app
