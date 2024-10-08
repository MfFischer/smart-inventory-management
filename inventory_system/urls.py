from flask import Blueprint
from modules.suppliers.views import get_suppliers

suppliers_bp = Blueprint('suppliers', __name__)

suppliers_bp.route('/suppliers', methods=['GET'])(get_suppliers)
