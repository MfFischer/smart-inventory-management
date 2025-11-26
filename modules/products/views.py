from flask import Blueprint, render_template
from flask_login import login_required
from flask_restx import Namespace, Resource

# Create a Blueprint for regular routes
products_bp = Blueprint('products', __name__)

# Create a Namespace for API routes
api = Namespace('products', description='Product operations')

@products_bp.route('/list')
@login_required
def products_list():
    # In a real application, you would fetch products from the database
    products = []  # Replace with actual product data
    return render_template('products/list.html', products=products)

# Example API endpoint
@api.route('/')
class ProductList(Resource):
    def get(self):
        """List all products"""
        return {'products': []}
