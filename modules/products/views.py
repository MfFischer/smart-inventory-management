from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from modules.products.models import Product
from modules.products.serializers import ProductSchema
from inventory_system import db
from modules.suppliers.models import Supplier
from modules.suppliers.serializers import SupplierSchema
from modules.inventory.models import Inventory

products_bp = Blueprint('products', __name__)

# Initialize the ProductSchema for validation
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Initialize the SupplierSchema for serialization
supplier_schema = SupplierSchema()

# Render all products for the HTML view
@products_bp.route('/', methods=['GET'])
def view_products():
    products = Product.query.all()
    return render_template('products.html', products=products)

# Get a product by ID and render the product details page
@products_bp.route('/<int:product_id>', methods=['GET'])
def product_details(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_details.html', product=product)

# Get all products (API endpoint for JSON response)
@products_bp.route('/api', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify(products_schema.dump(products)), 200


# Render the create product form
@products_bp.route('/create', methods=['GET'])
def create_product_form():
    return render_template('create_product.html')


# Handle the form submission to create a new product
@products_bp.route('/create', methods=['POST'])
def create_product():
    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    quantity_in_stock = request.form['quantity_in_stock']
    reorder_point = request.form['reorder_point']

    # Create a new Product instance
    new_product = Product(
        name=name,
        description=description,
        price=price,
        quantity_in_stock=quantity_in_stock,
        reorder_point=reorder_point
    )

    # Add and commit the product to the database
    db.session.add(new_product)
    db.session.commit()

    # Redirect to the products page
    return redirect(url_for('products.view_products'))

# Update a product by ID (API endpoint for JSON response)
@products_bp.route('/api/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json

    # Validate the incoming request data
    errors = product_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400

    # Check for duplicate product names if the name is being updated
    if 'name' in data and Product.query.filter(Product.id != product_id, Product.name == data['name']).first():
        return jsonify({"error": "A product with this name already exists."}), 400

    # Update the product with validated data
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    if 'price' in data:
        product.price = data['price']

    db.session.commit()
    return jsonify(product_schema.dump(product)), 200

# Update a product by ID (HTML form-based)
@products_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = request.form['price']
        product.quantity_in_stock = request.form['quantity_in_stock']
        product.reorder_point = request.form['reorder_point']

        db.session.commit()
        return redirect(url_for('products.product_details', product_id=product.id))

    return render_template('edit_product.html', product=product)

# Delete a product by ID
@products_bp.route('/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.sales:  # Check if the product has any associated sales
        return jsonify({"error": "Cannot delete a product with associated sales records."}), 400

    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('products.view_products'))


# Get products below reorder point based on quantity in stock
@products_bp.route('/api/reorder', methods=['GET'])
def get_products_below_reorder():
    """Get all products below their reorder point."""
    products_below_reorder = Product.query.filter(Product.quantity_in_stock <= Product.reorder_point).all()
    if not products_below_reorder:
        return jsonify({"message": "No products below reorder point"}), 404
    return products_schema.jsonify(products_below_reorder), 200

# Update the reorder point and reorder quantity of a product (API endpoint for JSON response)
@products_bp.route('/api/<int:product_id>/reorder_settings', methods=['PUT'])
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

# Search for products
@products_bp.route('/search', methods=['GET'])
def search_products():
    name = request.args.get('name')
    sku = request.args.get('sku')
    supplier_name = request.args.get('supplier')

    # Build the query for Product
    query = Product.query

    if name:
        query = query.filter(Product.name.ilike(f'%{name}%'))
    if sku:
        query = query.join(Inventory).filter(Inventory.sku.ilike(f'%{sku}%'))
    if supplier_name:
        query = query.join(Supplier).filter(Supplier.name.ilike(f'%{supplier_name}%'))

    products = query.all()

    # If only one product is found, redirect to product details page directly
    if len(products) == 1:
        return redirect(url_for('products.product_details', product_id=products[0].id))

    # If multiple products found or none, render the search results in HTML
    return render_template('products.html', products=products)

