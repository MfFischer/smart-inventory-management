from flask import Blueprint
from products.views import search_products

products_bp = Blueprint('products', __name__)

# Add search route
products_bp.add_url_rule('/search', view_func=search_products, methods=['GET'])
