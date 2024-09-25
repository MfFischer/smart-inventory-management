from flask import Blueprint, request, jsonify
from products.models import Product, InventoryMovement
from products.serializers import ProductSchema
from inventory_system import db
from suppliers.models import Supplier

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

    # Ensure price is provided and valid
    if 'price' not in data or data['price'] is None:
        return jsonify({"error": "The price field is required."}), 400

    # Create a new Product instance with validated data
    # Create a new Product instance with validated data
    new_product = Product(
        name=data.get('name'),
        description=data.get('description'),
        price=data.get('price')
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
    if 'price' in data:
        # Update price if provided
        product.price = data['price']

    db.session.commit()
    return jsonify(product_schema.dump(product)), 200

# Delete a product by ID
@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return '', 204

# Get products below reorder point based on quantity in stock
@products_bp.route('/reorder', methods=['GET'])
def get_products_below_reorder():
    """Get all products below their reorder point."""
    products_below_reorder = Product.query.filter(Product.quantity_in_stock <= Product.reorder_point).all()
    if not products_below_reorder:
        return jsonify({"message": "No products below reorder point"}), 404
    return products_schema.jsonify(products_below_reorder), 200

# Update the reorder point and reorder quantity of a product
@products_bp.route('/<int:product_id>/reorder_settings', methods=['PUT'])
def update_reorder_settings(product_id):
    """Update the reorder point and reorder quantity of a product."""
    product = Product.query.get_or_404(product_id)
    data = request.json
    if 'reorder_point' not in data or 'reorder_quantity' not in data:
        return jsonify({"message": "Reorder point and reorder quantity are required"}), 400

    product.reorder_point = data['reorder_point']
    product.reorder_quantity = data['reorder_quantity']
    db.session.commit()
    return product_schema.jsonify(product), 200

@products_bp.route('/search', methods=['GET'])
def search_products():
    """
    Search for products by name, SKU, or other attributes.
    """
    # Get query parameters
    name = request.args.get('name')
    sku = request.args.get('sku')
    supplier_name = request.args.get('supplier')

    # Build the query
    query = Product.query

    if name:
        query = query.filter(Product.name.ilike(f'%{name}%'))
    if sku:
        query = query.filter(Product.sku.ilike(f'%{sku}%'))
    if supplier_name:
        query = query.join(Supplier).filter(Supplier.name.ilike(f'%{supplier_name}%'))

    # Execute the query
    products = query.all()

    # Serialize the products
    products_data = []
    for product in products:
        product_data = product.to_dict()

        # Add last reorder date
        last_movement = InventoryMovement.query.filter_by(product_id=product.id).order_by(InventoryMovement.created_at.desc()).first()
        product_data['last_reorder_date'] = last_movement.created_at if last_movement else None

        # Add inventory movements (last 10)
        movements = InventoryMovement.query.filter_by(product_id=product.id).order_by(InventoryMovement.created_at.desc()).limit(10).all()
        product_data['inventory_movements'] = [{
            'movement_type': movement.movement_type,
            'quantity': movement.quantity,
            'date': movement.created_at
        } for movement in movements]

        # Add supplier information
        if product.supplier:
            product_data['supplier'] = {
                'name': product.supplier.name,
                'contact_info': product.supplier.contact_info
            }

        products_data.append(product_data)

    return jsonify(products_data), 200