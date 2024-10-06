from flask import jsonify, request
from flask_restx import Namespace, Resource, fields
from inventory_system import db
from modules.sales.models import Sale
from modules.sales.serializers import SaleSchema
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

# Define a namespace for sales-related API operations
api = Namespace('sales', description='Sales related operations')

# Initialize the SaleSchema for serialization
sale_schema = SaleSchema()
sales_schema = SaleSchema(many=True)

# Define the sale model for API documentation (for Swagger)
sale_model = api.model('Sale', {
    'product_id': fields.Integer(required=True, description='Product ID'),
    'quantity': fields.Integer(required=True, description='Quantity of the product sold'),
    'total_price': fields.Float(required=True, description='Total price of the sale'),
    'sale_status': fields.String(description='Status of the sale')
})

# API endpoint for getting all sales
@api.route('/api')
class SalesAPIList(Resource):
    @api.doc(responses={200: 'Success',
                        500: 'Internal Server Error'})
    def get(self):
        """Get all sales records (API endpoint)."""
        try:
            sales = Sale.query.all()
            return sales_schema.dump(sales), 200
        except SQLAlchemyError as db_err:
            print(f"Database error: {db_err}")
            return {
                'message': 'An error occurred while fetching sales records.'
            }, 500

    @api.expect(sale_model)
    @api.doc(responses={201: 'Created',
                        400: 'Validation Error',
                        415: 'Unsupported Media Type',
                        500: 'Internal Server Error'})
    def post(self):
        """Create a new sale record (API endpoint)."""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        try:
            sale_data = sale_schema.load(request.json)
            new_sale = Sale(
                product_id=sale_data['product_id'],
                quantity=sale_data['quantity'],
                total_price=sale_data['total_price'],
                sale_status=sale_data.get('sale_status', 'completed')
            )
            db.session.add(new_sale)
            db.session.commit()
            return sale_schema.dump(new_sale), 201
        except ValidationError as err:
            return err.messages, 400
        except SQLAlchemyError as db_err:
            print(f"Database error: {db_err}")
            return {
                'message': 'An error occurred while creating the sale record.'
            }, 500

# API endpoint for handling sale details by ID
@api.route('/api/<int:sale_id>')
class SaleDetailAPI(Resource):
    @api.doc(responses={200: 'Success',
                        404: 'Not Found',
                        500: 'Internal Server Error'})
    def get(self, sale_id):
        """Get a sale by ID (API endpoint)."""
        try:
            sale = Sale.query.get_or_404(sale_id)
            return sale_schema.dump(sale), 200
        except SQLAlchemyError as db_err:
            print(f"Database error: {db_err}")
            return {
                'message': 'An error occurred while fetching the sale record.'
            }, 500

    @api.expect(sale_model)
    @api.doc(responses={200: 'Success',
                        400: 'Validation Error',
                        404: 'Not Found',
                        415: 'Unsupported Media Type',
                        500: 'Internal Server Error'})
    def put(self, sale_id):
        """Update a sale record by ID (API endpoint)."""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        sale = Sale.query.get_or_404(sale_id)
        try:
            sale_data = sale_schema.load(request.json, partial=True)
            for key, value in sale_data.items():
                setattr(sale, key, value)
            db.session.commit()
            return sale_schema.dump(sale), 200
        except ValidationError as err:
            return err.messages, 400
        except SQLAlchemyError as db_err:
            db.session.rollback()  # Rollback the session in case of error
            print(f"Database error: {db_err}")
            return {
                'message': 'An error occurred while updating the sale record.'
            }, 500

    @api.doc(responses={204: 'No Content',
                        404: 'Not Found',
                        500: 'Internal Server Error'})
    def delete(self, sale_id):
        """Delete a sale by ID (API endpoint)."""
        sale = Sale.query.get_or_404(sale_id)
        try:
            db.session.delete(sale)
            db.session.commit()
            return '', 204
        except SQLAlchemyError as db_err:
            db.session.rollback()
            print(f"Database error: {db_err}")
            return {
                'message': 'An error occurred while deleting the sale record.'
            }, 500
