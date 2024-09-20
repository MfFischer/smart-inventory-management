from flask import jsonify, request, Blueprint
from inventory.models import Inventory
from inventory_system import db
from inventory.serializers import InventorySchema  # Import a schema for validation

inventory_bp = Blueprint('inventory', __name__)

# Initialize the InventorySchema for validating input and output
inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)

# Get all inventory items
@inventory_bp.route('/', methods=['GET'])
def get_inventory():
    inventory_items = Inventory.query.all()
    return jsonify(inventories_schema.dump(inventory_items)), 200

# Create a new inventory item
@inventory_bp.route('/', methods=['POST'])
def create_inventory_item():
    data = request.json

    # Validate the incoming request data
    errors = inventory_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Create a new Inventory instance with validated data
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
    return jsonify(inventory_schema.dump(new_item)), 201

# Get an inventory item by ID
@inventory_bp.route('/<int:item_id>', methods=['GET'])
def get_inventory_item(item_id):
    item = Inventory.query.get_or_404(item_id)
    return jsonify(inventory_schema.dump(item)), 200

# Update an inventory item by ID
@inventory_bp.route('/<int:item_id>', methods=['PUT'])
def update_inventory_item(item_id):
    item = Inventory.query.get_or_404(item_id)
    data = request.json

    # Validate the incoming request data
    errors = inventory_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400

    # Update the item with validated data
    item.product_id = data.get('product_id', item.product_id)
    item.supplier_id = data.get('supplier_id', item.supplier_id)
    item.sku = data.get('sku', item.sku)
    item.stock_quantity = data.get('stock_quantity', item.stock_quantity)
    item.reorder_threshold = data.get('reorder_threshold', item.reorder_threshold)
    item.unit_price = data.get('unit_price', item.unit_price)

    db.session.commit()
    return jsonify(inventory_schema.dump(item)), 200

# Delete an inventory item by ID
@inventory_bp.route('/<int:item_id>', methods=['DELETE'])
def delete_inventory_item(item_id):
    item = Inventory.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return '', 204
