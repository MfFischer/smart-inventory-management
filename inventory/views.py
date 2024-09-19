from flask import jsonify, request, Blueprint
from inventory.models import Inventory
from inventory_system import db

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory', methods=['GET'])
def get_inventory():
    inventory_items = Inventory.query.all()
    return jsonify([item.to_dict() for item in inventory_items]), 200

@inventory_bp.route('/inventory', methods=['POST'])
def create_inventory_item():
    data = request.json
    new_item = Inventory(
        product_id=data.get('product_id'),
        supplier_id=data.get('supplier_id'),
        sku=data.get('sku'),
        stock_quantity=data.get('stock_quantity'),
        reorder_threshold=data.get('reorder_threshold'),
        unit_price=data.get('unit_price')
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(new_item.to_dict()), 201
