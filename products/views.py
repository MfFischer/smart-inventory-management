from flask import Blueprint, request, jsonify
from products.models import Product
from products.serializers import ProductSchema
from inventory_system import db

products_bp = Blueprint('products', __name__)

# Initialize the ProductSchema for validation
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Get all products
@products_bp.route('/', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify(products_schema.dump(products)), 200

# Create a new product
@products_bp.route('/', methods=['POST'])
def create_product():
    data = request.json

    # Validate the incoming request data
    errors = product_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    # Check for duplicate product names
    if Product.query.filter_by(name=data.get('name')).first():
        return jsonify({"error": "A product with this name already exists."}), 400

    # Create a new Product instance with validated data
    new_product = Product(
        name=data.get('name'),
        description=data.get('description')
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify(product_schema.dump(new_product)), 201

# Get a product by ID
@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product_schema.dump(product)), 200

# Update a product by ID
@products_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json

    # Validate the incoming request data
    errors = product_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400

    # Check for duplicate product names if the name is being updated
    if 'name' in data and Product.query.filter(Product.id != product_id,
                                               Product.name == data['name']).first():
        return jsonify({"error": "A product with this name already exists."}), 400

    # Update the product with validated data
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    db.session.commit()
    return jsonify(product_schema.dump(product)), 200

# Delete a product by ID
@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return '', 204
