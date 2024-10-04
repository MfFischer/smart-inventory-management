from flask import (Blueprint, request, jsonify,
                   render_template, redirect, url_for)
from modules.sales.models import Sale
from modules.sales.serializers import SaleSchema
from inventory_system import db
from modules.products.models import Product

sales_bp = Blueprint('sales', __name__)

# Initialize the SaleSchema for validating input and output
sale_schema = SaleSchema()
sales_schema = SaleSchema(many=True)

# Render the sales page with optional search by date
@sales_bp.route('/', methods=['GET'])
def view_sales():
    search_date = request.args.get('date')
    if search_date:
        sales = Sale.query.filter(db.func.date(Sale.created_at) == search_date).all()
    else:
        sales = Sale.query.all()
    return render_template('sales.html', sales=sales)

# Get all sales records (API endpoint)
@sales_bp.route('/api', methods=['GET'])
def get_sales():
    sales = Sale.query.all()
    result = sales_schema.dump(sales)
    return jsonify(result), 200

# Create a new sale record (API endpoint)
@sales_bp.route('/api', methods=['POST'])
def create_sale():
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

# Get a sale by ID
@sales_bp.route('/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    result = sale_schema.dump(sale)
    return jsonify(result), 200

# update sale via API (PUT request)
@sales_bp.route('/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
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
    result = sale_schema.dump(sale)
    return jsonify(result), 200


@sales_bp.route('/add', methods=['GET', 'POST'])
def add_sale():
    if request.method == 'POST':
        # Get form data
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])

        # Fetch product price from the database
        product = Product.query.get(product_id)
        if not product:
            return "Product not found", 404

        # Calculate total price based on quantity and product price
        total_price = product.price * quantity

        # Create a new Sale instance
        new_sale = Sale(
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
            sale_status=request.form.get('sale_status', 'completed')
        )
        db.session.add(new_sale)
        # Deduct the quantity from the product's stock
        product.quantity_in_stock -= quantity

        # Commit the changes to both the sale and product stock
        db.session.commit()

        return redirect(url_for('sales.view_sales'))

    # If it's a GET request, fetch all products to show in the form
    products = Product.query.all()
    return render_template('add_sale.html', products=products)

# Edit sale
@sales_bp.route('/<int:sale_id>/edit', methods=['GET', 'POST'])
def edit_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    if request.method == 'POST':
        quantity = int(request.form['quantity'])

        # Fetch the product to get its price
        product = Product.query.get(sale.product_id)
        if not product:
            return "Product not found", 404

        # Calculate the new total price based on the updated quantity
        total_price = product.price * quantity

        # Update the sale details
        sale.quantity = quantity
        sale.total_price = total_price
        sale.sale_status = request.form['sale_status']

        db.session.commit()

        return redirect(url_for('sales.view_sales'))

    return render_template('edit_sale.html', sale=sale)


# Delete sale
@sales_bp.route('/<int:sale_id>/delete', methods=['POST'])
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    return redirect(url_for('sales.view_sales'))

# Search sales by date or other criteria
@sales_bp.route('/search', methods=['GET'])
def search_sales():
    query = Sale.query

    # Example: Search by sale date or other criteria
    date = request.args.get('date')

    if date:
        query = query.filter(Sale.created_at.like(f"%{date}%"))

    sales = query.all()

    return render_template('sales.html', sales=sales)

