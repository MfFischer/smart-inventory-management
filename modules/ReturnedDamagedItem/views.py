from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from inventory_system import db
from modules.inventory.models import Inventory
from modules.sales.models import Sale
from modules.users.models import User
from modules.ReturnedDamagedItem.models import ReturnedDamagedItem  # Import the model

# Create a Namespace for returned/damaged items with Swagger documentation
api = Namespace('returned_damaged', description='Operations for managing returned or damaged items')

# Define the model for API documentation
returned_damaged_item_model = api.model('ReturnedDamagedItem', {
    'inventory_id': fields.Integer(required=True, description='Inventory ID of the item'),
    'sale_id': fields.Integer(required=False, description='Sale ID linked to the return for proof of purchase'),
    'quantity': fields.Integer(required=True, description='Quantity of items returned or damaged'),
    'reason': fields.String(required=True, description='Reason for return or damage'),
    'return_date': fields.DateTime(description='Date the item was returned or marked as damaged'),
    'user_id': fields.Integer(required=True, description='ID of the user who recorded the return')
})


# CRUD operations
@api.route('/')
class ReturnedDamagedItemList(Resource):
    @api.doc('list_returned_damaged_items')
    @api.marshal_list_with(returned_damaged_item_model)
    def get(self):
        """Retrieve all returned/damaged items."""
        returned_damaged_items = ReturnedDamagedItem.query.all()
        return returned_damaged_items, 200

    @api.expect(returned_damaged_item_model)
    @api.doc('create_returned_damaged_item')
    def post(self):
        """Create a new returned/damaged item entry."""
        data = request.json
        try:
            # Validate and check related fields
            inventory = Inventory.query.get(data['inventory_id'])
            if not inventory:
                return {'message': 'Inventory item not found'}, 404

            sale = None
            if 'sale_id' in data and data['sale_id']:
                sale = Sale.query.get(data['sale_id'])
                if not sale:
                    return {'message': 'Sale record not found'}, 404

            user = User.query.get(data['user_id'])
            if not user:
                return {'message': 'User not found'}, 404

            # Create the returned/damaged item
            new_returned_item = ReturnedDamagedItem(
                inventory_id=data['inventory_id'],
                sale_id=data.get('sale_id'),
                quantity=data['quantity'],
                reason=data['reason'],
                user_id=data['user_id'],
                return_date=data.get('return_date', None)
            )

            db.session.add(new_returned_item)
            db.session.commit()
            return {'message': 'Returned/damaged item created successfully'}, 201

        except Exception as e:
            db.session.rollback()
            return {'message': f'An error occurred: {str(e)}'}, 500


@api.route('/<int:item_id>')
@api.param('item_id', 'The Returned/Damaged Item identifier')
class ReturnedDamagedItemResource(Resource):
    @api.doc('get_returned_damaged_item')
    @api.marshal_with(returned_damaged_item_model)
    def get(self, item_id):
        """Retrieve a specific returned/damaged item by ID."""
        returned_damaged_item = ReturnedDamagedItem.query.get_or_404(item_id)
        return returned_damaged_item, 200

    @api.expect(returned_damaged_item_model)
    @api.doc('update_returned_damaged_item')
    def put(self, item_id):
        """Update a returned/damaged item."""
        data = request.json
        returned_damaged_item = ReturnedDamagedItem.query.get_or_404(item_id)

        try:
            # Update fields if provided
            if 'inventory_id' in data:
                inventory = Inventory.query.get(data['inventory_id'])
                if not inventory:
                    return {'message': 'Inventory item not found'}, 404
                returned_damaged_item.inventory_id = data['inventory_id']

            if 'sale_id' in data:
                sale = Sale.query.get(data['sale_id'])
                if not sale:
                    return {'message': 'Sale record not found'}, 404
                returned_damaged_item.sale_id = data['sale_id']

            if 'quantity' in data:
                returned_damaged_item.quantity = data['quantity']

            if 'reason' in data:
                returned_damaged_item.reason = data['reason']

            if 'return_date' in data:
                returned_damaged_item.return_date = data['return_date']

            db.session.commit()
            return {'message': 'Returned/damaged item updated successfully'}, 200

        except Exception as e:
            db.session.rollback()
            return {'message': f'An error occurred: {str(e)}'}, 500

    @api.doc('delete_returned_damaged_item')
    def delete(self, item_id):
        """Delete a specific returned/damaged item by ID."""
        returned_damaged_item = ReturnedDamagedItem.query.get_or_404(item_id)

        try:
            db.session.delete(returned_damaged_item)
            db.session.commit()
            return {'message': 'Returned/damaged item deleted successfully'}, 204

        except Exception as e:
            db.session.rollback()
            return {'message': f'An error occurred: {str(e)}'}, 500
