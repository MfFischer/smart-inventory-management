from flask import Flask, render_template, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_restx import Api
import os
from .swagger import init_swagger

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

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

    app.config.from_object('inventory_system.settings')

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Root route for Swagger JSON
    @app.route('/')
    def home():
        return render_template('index.html')

    # API Blueprint and Namespace Registration
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    api = Api(api_bp,
              title="Smart Inventory System API",
              version="1.0",
              description="API for managing inventory, products, sales, and users."
              )

    from modules.products.views import api as products_ns
    from modules.suppliers.views import api as suppliers_ns
    from modules.inventory.views import api as inventory_ns
    from modules.sales.views import api as sales_ns
    from modules.users.views import api as users_ns

    # Register API namespaces (for API routes)
    api.add_namespace(products_ns, path='/products')
    api.add_namespace(suppliers_ns, path='/suppliers')
    api.add_namespace(inventory_ns, path='/inventory')
    api.add_namespace(sales_ns, path='/sales')
    api.add_namespace(users_ns, path='/users')

    app.register_blueprint(api_bp)

    # Main routes blueprint
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # Main routes blueprint (for HTML views)
    from modules.routes.products_routes import products_bp
    from modules.routes.sales_routes import sales_bp
    from modules.routes.inventory_routes import inventory_bp
    from modules.routes.users_routes import users_bp
    from modules.routes.suppliers_routes import suppliers_bp


    # Register HTML routes
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')

    init_swagger(app)

    return app
