from flask import Blueprint, render_template, request, redirect, url_for
from modules.products.models import Product
from modules.suppliers.models import Supplier
from modules.inventory.models import Inventory
from inventory_system import db
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/')
def inventory_list():
    """Render the inventory page with all inventory items."""
    try:
        inventory_items = Inventory.query.all()
        return render_template('inventory.html',
                               inventory_items=inventory_items)
    except Exception as e:
        print(f"Error fetching inventory items: {e}")
        return render_template('error.html'), 500


@inventory_bp.route('/create', methods=['GET', 'POST'])
def inventory_create():
    """Render the form to create a new inventory item."""
    if request.method == 'POST':
        try:
            # Fetch product details if an existing product is selected
            product_id = request.form.get('product_id')
            if product_id == 'new':
                # Add a new product
                new_product = Product(
                    name=request.form['new_product_name'],
                    description=request.form.get('new_product_description', ''),
                    price=request.form['unit_price']
                )
                db.session.add(new_product)
                db.session.commit()
                product_id = new_product.id  # Update product_id to the new product's ID
                # Set initial values for new product inventory fields
                stock_quantity = request.form.get('stock_quantity', 0)
                reorder_threshold = request.form.get('reorder_threshold', 0)
                unit_price = request.form.get('unit_price', 0.0)
            else:
                # Use existing product and set inventory fields as defaults
                product = Product.query.get(product_id)
                if product:
                    stock_quantity = int(request.form.get('stock_quantity', product.quantity_in_stock))
                    reorder_threshold = int(request.form.get('reorder_threshold', product.reorder_point))
                    unit_price = float(request.form.get('unit_price', product.price))
                else:
                    return "Product not found", 404

            # Check supplier selection or create a new supplier
            supplier_id = request.form.get('supplier_id')
            if supplier_id == 'new':
                new_supplier = Supplier(
                    name=request.form['new_supplier_name'],
                    contact=request.form.get('new_supplier_contact', '')
                )
                db.session.add(new_supplier)
                db.session.commit()
                supplier_id = new_supplier.id
            else:
                supplier_id = request.form['supplier_id']

            # Create the new inventory item
            new_item = Inventory(
                product_id=product_id,
                supplier_id=supplier_id,
                sku=request.form['sku'],
                stock_quantity=int(stock_quantity),
                reorder_threshold=int(reorder_threshold),
                unit_price=float(unit_price)
            )
            db.session.add(new_item)
            db.session.commit()

            return redirect(url_for('inventory.inventory_list'))
        except Exception as e:
            db.session.rollback()
            return render_template('create_inventory_item.html',
                                   error=str(e))

    # Fetch all products and suppliers for the dropdowns
    products = Product.query.all()
    suppliers = Supplier.query.all()
    return render_template('create_inventory_item.html',
                           products=products,
                           suppliers=suppliers)

@inventory_bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
def inventory_edit(item_id):
    """Render form to edit an inventory item."""
    item = Inventory.query.get_or_404(item_id)

    if request.method == 'POST':
        try:
            item.product_id = request.form['product_id']
            item.supplier_id = request.form['supplier_id']
            item.sku = request.form['sku']
            item.stock_quantity = request.form['stock_quantity']
            item.reorder_threshold = request.form['reorder_threshold']
            item.unit_price = request.form['unit_price']

            db.session.commit()
            return redirect(url_for('inventory.inventory_list'))
        except Exception as e:
            db.session.rollback()
            return render_template('edit_inventory.html',
                                   error=str(e),
                                   item=item)

    products = Product.query.all()
    suppliers = Supplier.query.all()
    return render_template('edit_inventory.html',
                           item=item, products=products,
                           suppliers=suppliers)


@inventory_bp.route('/<int:item_id>/delete', methods=['POST'])
def inventory_delete(item_id):
    """Delete an inventory item."""
    item = Inventory.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('inventory.inventory_list'))


@inventory_bp.route('/low-stock-alerts')
def low_stock_alerts():
    """Display low stock alerts."""
    try:
        low_stock_items = Inventory.query.filter(
            Inventory.stock_quantity <= Inventory.reorder_threshold
        ).all()
        return render_template('low_stock_alerts.html',
                               low_stock_items=low_stock_items)
    except Exception as e:
        print(f"Error fetching low stock alerts: {e}")
        return render_template('error.html'), 500


@inventory_bp.route('/search')
def inventory_search():
    """Search for inventory items by product name."""
    search_query = request.args.get('search')
    if search_query:
        inventory_items = Inventory.query.filter(
            Inventory.product.name.ilike(f'%{search_query}%')
        ).all()
    else:
        inventory_items = Inventory.query.all()
    return render_template('inventory.html',
                           inventory_items=inventory_items)


@inventory_bp.route('/<int:item_id>/reorder', methods=['GET', 'POST'])
def inventory_reorder(item_id):
    """Handle reorder operations for an inventory item."""
    item = Inventory.query.get_or_404(item_id)
    if request.method == 'POST':
        item.last_reordered_at = datetime.now()
        item.stock_quantity += item.product.reorder_quantity  # Increment stock by reorder quantity
        db.session.commit()
        return redirect(url_for('inventory.inventory_list'))

    supplier_email = item.supplier.email if item.supplier else None
    reorder_quantity = item.product.reorder_quantity if item.product else 0
    return render_template('reorder_form.html',
                           item=item,
                           supplier_email=supplier_email,
                           reorder_quantity=reorder_quantity)

@inventory_bp.route('/product-details/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    """Fetch product details by ID."""
    product = Product.query.get(product_id)
    if product:
        return {
            'success': True,
            'product': {
                'stock_quantity': product.quantity_in_stock,
                'reorder_threshold': product.reorder_point,
                'unit_price': product.price
            }
        }
    else:
        return {'success': False, 'error': 'Product not found'}, 404

