from flask import Blueprint, request, jsonify
from modules.sales.models import Sale
from modules.sales.serializers import SaleSchema
from inventory_system import db

sales_bp = Blueprint('sales', __name__)

# Initialize the SaleSchema for validating input and output
sale_schema = SaleSchema()
sales_schema = SaleSchema(many=True)

# Get all sales records
@sales_bp.route('/', methods=['GET'])
def get_sales():
    sales = Sale.query.all()
    # Use `dump` to serialize the list of sales
    result = sales_schema.dump(sales)
    # Use Flask's jsonify to return the serialized data
    return jsonify(result), 200

# Create a new sale record
@sales_bp.route('/', methods=['POST'])
def create_sale():
    # Validate the incoming request data
    data = request.json
    errors = sale_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Create a new Sale instance with validated data
    new_sale = Sale(
        product_id=data['product_id'],
        quantity=data['quantity'],
        total_price=data['total_price'],
        sale_status=data.get('sale_status', 'completed')
    )
    db.session.add(new_sale)
    db.session.commit()
    result = sale_schema.dump(new_sale)
    return jsonify(result), 201

# Get a sale by ID
@sales_bp.route('/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    result = sale_schema.dump(sale)
    return jsonify(result), 200

# Update a sale by ID
@sales_bp.route('/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    # Validate the incoming request data
    data = request.json
    errors = sale_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400

    # Update the sale instance with validated data
    sale.product_id = data.get('product_id', sale.product_id)
    sale.quantity = data.get('quantity', sale.quantity)
    sale.total_price = data.get('total_price', sale.total_price)
    sale.sale_status = data.get('sale_status', sale.sale_status)

    db.session.commit()
    result = sale_schema.dump(sale)
    return jsonify(result), 200

# Delete a sale by ID
@sales_bp.route('/<int:sale_id>', methods=['DELETE'])
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    return '', 204
