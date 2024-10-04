from flask import Blueprint
from modules.sales.views import view_sales, create_sale, get_sale, update_sale, delete_sale

sales_bp = Blueprint('sales', __name__)

# Add the sales page view (HTML view)
sales_bp.add_url_rule('/', view_func=view_sales, methods=['GET'])

# Add the API routes for sales
sales_bp.add_url_rule('/api', view_func=create_sale, methods=['POST'])
sales_bp.add_url_rule('/api/<int:sale_id>', view_func=get_sale, methods=['GET'])
sales_bp.add_url_rule('/api/<int:sale_id>', view_func=update_sale, methods=['PUT'])
sales_bp.add_url_rule('/api/<int:sale_id>', view_func=delete_sale, methods=['DELETE'])
