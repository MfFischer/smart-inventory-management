from flask import Blueprint, request, jsonify
from products.models import Product
from inventory_system import db

products_bp = Blueprint('products', __name__)

# Get all products
@products_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products]), 200

# Create a new product
@products_bp.route('/products', methods=['POST'])
def create_product():
    data = request.json
    new_product = Product(
        name=data.get('name'),
        description=data.get('description')
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201

# Get a product by ID
@products_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict()), 200

# Update a product by ID
@products_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    db.session.commit()
    return jsonify(product.to_dict()), 200

# Delete a product by ID
@products_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return '', 204
