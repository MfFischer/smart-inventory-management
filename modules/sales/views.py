from flask import jsonify, request
from flask_restx import Namespace, Resource
from inventory_system import db
from modules.sales.models import Sale
from modules.sales.serializers import SaleSchema

# Define a namespace for sales-related API operations
api = Namespace('sales', description='Sales related operations')

# Initialize the SaleSchema for serialization
sale_schema = SaleSchema()
sales_schema = SaleSchema(many=True)

# API endpoint for getting all sales
@api.route('/api')
class SalesAPIList(Resource):
    def get(self):
        """Get all sales records (API endpoint)."""
        sales = Sale.query.all()
        return jsonify(sales_schema.dump(sales)), 200

    def post(self):
        """Create a new sale record (API endpoint)."""
        data = request.json
        errors = sale_schema.validate(data)
        if errors:
            return jsonify(errors), 400

        new_sale = Sale(
            product_id=data['product_id'],
            quantity=data['quantity'],
            total_price=data['total_price'],
            sale_status=data.get('sale_status', 'completed')
        )
        db.session.add(new_sale)
        db.session.commit()
        return jsonify(sale_schema.dump(new_sale)), 201

# API endpoint for handling sale details by ID
@api.route('/api/<int:sale_id>')
class SaleDetailAPI(Resource):
    def get(self, sale_id):
        """Get a sale by ID (API endpoint)."""
        sale = Sale.query.get_or_404(sale_id)
        return jsonify(sale_schema.dump(sale)), 200

    def put(self, sale_id):
        """Update a sale record by ID (API endpoint)."""
        sale = Sale.query.get_or_404(sale_id)
        data = request.json
        errors = sale_schema.validate(data, partial=True)
        if errors:
            return jsonify(errors), 400

        sale.product_id = data.get('product_id', sale.product_id)
        sale.quantity = data.get('quantity', sale.quantity)
        sale.total_price = data.get('total_price', sale.total_price)
        sale.sale_status = data.get('sale_status', sale.sale_status)

        db.session.commit()
        return jsonify(sale_schema.dump(sale)), 200

    def delete(self, sale_id):
        """Delete a sale by ID (API endpoint)."""
        sale = Sale.query.get_or_404(sale_id)
        db.session.delete(sale)
        db.session.commit()
        return '', 204
