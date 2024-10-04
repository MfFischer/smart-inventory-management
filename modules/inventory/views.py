from flask import (jsonify, request, Blueprint, render_template,
                   redirect, url_for)
from modules.products.models import Product
from modules.suppliers.models import Supplier
from modules.inventory.models import Inventory
from inventory_system import db
from modules.inventory.serializers import InventorySchema
from sqlalchemy.orm import joinedload
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)

# Initialize InventorySchema instances for serialization and deserialization
inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)

# Get all inventory items
@inventory_bp.route('/', methods=['GET'])
def get_inventory():
    try:
        # Fetch all inventory items with their associated products
        inventory_items = Inventory.query.options(
            joinedload(Inventory.product)
        ).all()
        return render_template(
            'inventory.html',
            inventory_items=inventory_items
        )
    except Exception as e:
        # Log any error that occurs and render an error page
        print(f"Error fetching inventory items: {e}")
        return render_template('error.html'), 500

# Create a new inventory item
@inventory_bp.route('/create', methods=['GET', 'POST'])
def create_inventory_item():
    if request.method == 'POST':
        try:
            # Handle both form and JSON data input
            data = request.form if request.content_type != 'application/json' else request.json

            # Check if a new product needs to be created
            if data.get('product_id') == 'new':
                new_product = Product(
                    name=data.get('new_product_name'),
                    description=data.get('new_product_description')
                )
                db.session.add(new_product)
                db.session.flush()  # Assigns an ID to the new product
                product_id = new_product.id
            else:
                product_id = int(data.get('product_id'))

            # Check if a new supplier needs to be created
            if data.get('supplier_id') == 'new':
                new_supplier = Supplier(
                    name=data.get('new_supplier_name'),
                    contact=data.get('new_supplier_contact')
                )
                db.session.add(new_supplier)
                db.session.flush()  # Assigns an ID to the new supplier
                supplier_id = new_supplier.id
            else:
                supplier_id = int(data.get('supplier_id'))

            # Ensure no duplicate SKU exists in the database
            existing_item = Inventory.query.filter_by(sku=data.get('sku')).first()
            if existing_item:
                error_message = f"An item with SKU '{data.get('sku')}' already exists."
                if request.content_type == 'application/json':
                    return jsonify({"error": error_message}), 400
                else:
                    return render_template(
                        'create_inventory_item.html',
                        error=error_message
                    )

            # Create a new inventory item
            new_item = Inventory(
                product_id=product_id,
                supplier_id=supplier_id,
                sku=data.get('sku'),
                stock_quantity=int(data.get('stock_quantity')),
                reorder_threshold=int(data.get('reorder_threshold')),
                unit_price=float(data.get('unit_price'))
            )
            db.session.add(new_item)
            db.session.commit()

            if request.content_type == 'application/json':
                return jsonify(inventory_schema.dump(new_item)), 201
            else:
                return redirect(url_for('inventory.get_inventory'))

        except Exception as e:
            # Rollback in case of any error during the database transaction
            db.session.rollback()
            error_message = f"An error occurred: {str(e)}"
            if request.content_type == 'application/json':
                return jsonify({"error": error_message}), 500
            else:
                return render_template(
                    'create_inventory_item.html',
                    error=error_message
                )

    # For GET requests, fetch products and suppliers to populate the form dropdowns
    products = Product.query.all()
    suppliers = Supplier.query.all()
    return render_template(
        'create_inventory_item.html',
        products=products,
        suppliers=suppliers
    )

# Get a single inventory item by ID
@inventory_bp.route('/<int:item_id>', methods=['GET'])
def get_inventory_item(item_id):
    # Fetch inventory item by ID or return 404 if not found
    item = Inventory.query.get_or_404(item_id)
    return jsonify(inventory_schema.dump(item)), 200

# Update an inventory item by ID
@inventory_bp.route('/<int:item_id>', methods=['PUT'])
def update_inventory_item(item_id):
    # Fetch the inventory item by ID
    item = Inventory.query.get_or_404(item_id)
    data = request.json

    # Validate the incoming data before updating
    errors = inventory_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400

    # Update the inventory item with the validated data
    item.product_id = data.get('product_id', item.product_id)
    item.supplier_id = data.get('supplier_id', item.supplier_id)
    item.sku = data.get('sku', item.sku)
    item.stock_quantity = data.get('stock_quantity', item.stock_quantity)
    item.reorder_threshold = data.get('reorder_threshold', item.reorder_threshold)
    item.unit_price = data.get('unit_price', item.unit_price)

    db.session.commit()
    return jsonify(inventory_schema.dump(item)), 200

# Delete an inventory item by ID
@inventory_bp.route('/<int:item_id>/delete', methods=['POST'])
def delete_inventory_item(item_id):
    # Fetch the inventory item and delete it from the database
    item = Inventory.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('inventory.get_inventory'))

# View details of an inventory item
@inventory_bp.route('/inventory/<int:item_id>', methods=['GET'])
def inventory_details(item_id):
    # Fetch the inventory item and render its details
    item = Inventory.query.get_or_404(item_id)
    return render_template('inventory_details.html', item=item)

# Search for inventory items by product name
@inventory_bp.route('/search', methods=['GET'])
def search_inventory():
    # Get the search query from request parameters
    search_query = request.args.get('search')
    if search_query:
        # Use ilike to perform a case-insensitive search
        inventory_items = Inventory.query.filter(
            Inventory.product.name.ilike(f'%{search_query}%')
        ).all()
    else:
        inventory_items = Inventory.query.all()
    return render_template(
        'inventory.html',
        inventory_items=inventory_items
    )

# Edit an existing inventory item
@inventory_bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_inventory_item(item_id):
    # Fetch the inventory item by ID or return 404 if not found
    item = Inventory.query.get_or_404(item_id)

    if request.method == 'POST':
        # Capture form data for the inventory item update
        product_id = request.form.get('product_id')
        supplier_id = request.form.get('supplier_id')

        # Validate the selected product and supplier
        product = Product.query.get(product_id)
        supplier = Supplier.query.get(supplier_id)

        if not product:
            return "Invalid product selected", 400
        if not supplier:
            return "Invalid supplier selected", 400

        # Update inventory item fields
        item.product_id = product.id
        item.supplier_id = supplier.id
        item.sku = request.form.get('sku')
        item.stock_quantity = request.form.get('stock_quantity')
        item.reorder_threshold = request.form.get('reorder_threshold')
        item.unit_price = request.form.get('unit_price')

        db.session.commit()

        return redirect(url_for('inventory.get_inventory'))

    # Fetch products and suppliers to populate the dropdowns in the form
    products = Product.query.all()
    suppliers = Supplier.query.all()

    return render_template(
        'edit_inventory.html',
        item=item, products=products,
        suppliers=suppliers
    )

# Display low stock alerts
@inventory_bp.route('/low-stock-alerts', methods=['GET'])
def low_stock_alerts():
    try:
        # Query items where stock quantity is below or equal to the reorder threshold
        low_stock_items = Inventory.query.filter(
            Inventory.stock_quantity <= Inventory.reorder_threshold
        ).all()

        return render_template(
            'low_stock_alerts.html',
            low_stock_items=low_stock_items
        )
    except Exception as e:
        # Log any error and render an error page
        print(f"Error fetching low stock alerts: {e}")
        return render_template('error.html'), 500

# Reorder an inventory item
@inventory_bp.route('/<int:item_id>/reorder', methods=['GET', 'POST'])
def reorder_item(item_id):
    # Fetch the inventory item by ID
    item = Inventory.query.get_or_404(item_id)

    if request.method == 'POST':
        # Fetch form data for reorder
        supplier_email = request.form.get('supplier_email')
        reorder_quantity = request.form.get('reorder_quantity')
        product_name = request.form.get('product_name')

        # Update the reorder date for the inventory item
        item.last_reordered_at = datetime.now()
        db.session.commit()

        return redirect(url_for('inventory.get_inventory'))

    # Get supplier email and reorder quantity for the reorder form
    supplier_email = item.supplier.email if item.supplier else None
    reorder_quantity = item.product.reorder_quantity if item.product else 0

    return render_template(
        'reorder_form.html',
        item=item, supplier_email=supplier_email,
        reorder_quantity=reorder_quantity
    )
