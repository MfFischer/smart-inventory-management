from flask import jsonify, request
from flask_restx import Namespace, Resource
from modules.inventory.models import Inventory
from inventory_system import db
from modules.inventory.serializers import InventorySchema

# Define a namespace for the inventory-related API
api = Namespace('inventory', description='Inventory related operations')

# Initialize InventorySchema instances for serialization and deserialization
inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)

@api.route('/')
class InventoryList(Resource):
    def get(self):
        """Get all inventory items (API)."""
        inventory_items = Inventory.query.all()
        return jsonify(inventories_schema.dump(inventory_items)), 200

    def post(self):
        """Create a new inventory item (API)."""
        data = request.json
        errors = inventory_schema.validate(data)
        if errors:
            return jsonify(errors), 400

        new_item = Inventory(
            product_id=data['product_id'],
            supplier_id=data['supplier_id'],
            sku=data['sku'],
            stock_quantity=data['stock_quantity'],
            reorder_threshold=data['reorder_threshold'],
            unit_price=data['unit_price']
        )
        db.session.add(new_item)
        db.session.commit()

        return jsonify(inventory_schema.dump(new_item)), 201

@api.route('/<int:item_id>')
class InventoryItem(Resource):
    def get(self, item_id):
        """Get a single inventory item by ID (API)."""
        item = Inventory.query.get_or_404(item_id)
        return jsonify(inventory_schema.dump(item)), 200

    def put(self, item_id):
        """Update an inventory item by ID (API)."""
        item = Inventory.query.get_or_404(item_id)
        data = request.json

        errors = inventory_schema.validate(data, partial=True)
        if errors:
            return jsonify(errors), 400

        item.product_id = data.get('product_id', item.product_id)
        item.supplier_id = data.get('supplier_id', item.supplier_id)
        item.sku = data.get('sku', item.sku)
        item.stock_quantity = data.get('stock_quantity', item.stock_quantity)
        item.reorder_threshold = data.get('reorder_threshold', item.reorder_threshold)
        item.unit_price = data.get('unit_price', item.unit_price)

        db.session.commit()
        return jsonify(inventory_schema.dump(item)), 200

    def delete(self, item_id):
        """Delete an inventory item by ID (API)."""
        item = Inventory.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return '', 204
