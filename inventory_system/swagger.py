from flask_restx import Api
from flask import Blueprint

# Define a blueprint for the Swagger API
swagger_bp = Blueprint('swagger', __name__)

# Initialize the Flask-RESTX API
api = Api(
    swagger_bp,
    title='Smart Inventory API',
    version='1.0',
    description='API documentation for the Smart Inventory System'
)

# Add the function to initialize Swagger with the Flask app
def init_swagger(app):
    """
    This function registers the Swagger blueprint with the Flask app.
    It ensures that the blueprint is only registered once.
    """
    # Use a unique name for the blueprint registration
    if 'swagger' not in app.blueprints:
        app.register_blueprint(swagger_bp, url_prefix='/api')

    from modules.products.views import api as products_ns
    from modules.suppliers.views import api as suppliers_ns
    from modules.inventory.views import api as inventory_ns
    from modules.sales.views import api as sales_ns
    from modules.users.views import api as users_ns

    # Register namespaces
    api.add_namespace(products_ns, path='/api/products')
    api.add_namespace(suppliers_ns, path='/api/suppliers')
    api.add_namespace(inventory_ns, path='/api/inventory')
    api.add_namespace(sales_ns, path='/api/sales')
    api.add_namespace(users_ns, path='/api/users')

