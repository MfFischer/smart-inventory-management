from flask import jsonify, request
from flask_restx import Namespace, Resource, fields
from modules.inventory.models import Inventory
from inventory_system import db
from modules.inventory.serializers import InventorySchema
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

# Define a namespace for inventory-related API operations
api = Namespace('inventory', description='Inventory related operations')

# Initialize the InventorySchema for serialization
inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)

# Define the inventory model for API documentation
inventory_model = api.model('Inventory', {
    'product_id': fields.Integer(required=True, description='Product ID'),
    'supplier_id': fields.Integer(required=False, description='Supplier ID (nullable)'),
    'sku': fields.String(required=True, description='Stock Keeping Unit (SKU)'),
    'stock_quantity': fields.Integer(required=True, description='Stock quantity'),
    'reorder_threshold': fields.Integer(required=True, description='Reorder threshold'),
    'unit_price': fields.Float(required=True, description='Unit price')
})

@api.route('/')
class InventoryList(Resource):
    @api.doc(responses={200: 'Success', 500: 'Server Error'})
    def get(self):
        """Retrieve all inventory items"""
        inventory_items = Inventory.query.all()
        return inventories_schema.dump(inventory_items), 200

    @api.expect(inventory_model)
    @api.doc(responses={201: 'Created',
                        400: 'Validation Error',
                        415: 'Unsupported Media Type',
                        500: 'Server Error'})
    def post(self):
        """Create a new inventory item"""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        try:
            inventory_data = inventory_schema.load(request.json)
            new_inventory = Inventory(**inventory_data)
            db.session.add(new_inventory)
            db.session.commit()
            return inventory_schema.dump(new_inventory), 201
        except ValidationError as err:
            return err.messages, 400

@api.route('/<int:item_id>')
class InventoryItem(Resource):
    @api.doc(responses={200: 'Success',
                        404: 'Not Found',
                        500: 'Server Error'})
    def get(self, item_id):
        """Retrieve a specific inventory item by ID"""
        inventory_item = Inventory.query.get_or_404(item_id)
        return inventory_schema.dump(inventory_item), 200

    @api.expect(inventory_model)
    @api.doc(responses={200: 'Success',
                        400: 'Validation Error',
                        404: 'Not Found',
                        415: 'Unsupported Media Type',
                        500: 'Server Error'})
    def put(self, item_id):
        """Update an existing inventory item by ID"""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        inventory_item = Inventory.query.get_or_404(item_id)
        try:
            # Load the data from the request (partial=True allows partial updates)
            inventory_data = inventory_schema.load(request.json, partial=True)

            # Print or log the data to be updated (for debugging)
            print(f"Updating inventory item {item_id} with data: {inventory_data}")

            # Iterate through the received data and update the fields in the inventory item
            for key, value in inventory_data.items():
                setattr(inventory_item, key, value)

            # Commit the changes to the database
            db.session.commit()

            # Print or log the result after commit (for debugging)
            print(f"Successfully updated inventory item {item_id}")

            return inventory_schema.dump(inventory_item), 200

        except ValidationError as err:
            # Handle validation errors
            return err.messages, 400

        except SQLAlchemyError as db_err:
            # Catch and log any SQLAlchemy errors
            db.session.rollback()  # Rollback the session if there's an error
            print(f"Database error: {db_err}")
            return {
                'message': 'An error occurred while updating the item. Please try again.'
            }, 500

    @api.doc(responses={204: 'No Content',
                        404: 'Not Found',
                        500: 'Server Error'})
    def delete(self, item_id):
        """Delete an inventory item by ID"""
        inventory_item = Inventory.query.get_or_404(item_id)
        db.session.delete(inventory_item)
        db.session.commit()
        return '', 204
