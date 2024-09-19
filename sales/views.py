from flask import Blueprint, request, jsonify
from sales.models import Sale
from inventory_system import db

sales_bp = Blueprint('sales', __name__)

# Get all sales records
@sales_bp.route('/sales', methods=['GET'])
def get_sales():
    sales = Sale.query.all()
    return jsonify([sale.to_dict() for sale in sales]), 200

# Create a new sale record
@sales_bp.route('/sales', methods=['POST'])
def create_sale():
    data = request.json
    new_sale = Sale(
        product_id=data.get('product_id'),
        quantity=data.get('quantity'),
        total_price=data.get('total_price'),
        sale_status=data.get('sale_status', 'completed')
    )
    db.session.add(new_sale)
    db.session.commit()
    return jsonify(new_sale.to_dict()), 201

# Get a sale by ID
@sales_bp.route('/sales/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return jsonify(sale.to_dict()), 200

# Update a sale by ID
@sales_bp.route('/sales/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    data = request.json
    sale.product_id = data.get('product_id', sale.product_id)
    sale.quantity = data.get('quantity', sale.quantity)
    sale.total_price = data.get('total_price', sale.total_price)
    sale.sale_status = data.get('sale_status', sale.sale_status)
    db.session.commit()
    return jsonify(sale.to_dict()), 200

# Delete a sale by ID
@sales_bp.route('/sales/<int:sale_id>', methods=['DELETE'])
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    return '', 204
