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
            product_id = request.form['product_id']
            supplier_id = request.form['supplier_id']

            new_item = Inventory(
                product_id=product_id,
                supplier_id=supplier_id,
                sku=request.form['sku'],
                stock_quantity=int(request.form['stock_quantity']),
                reorder_threshold=int(request.form['reorder_threshold']),
                unit_price=float(request.form['unit_price'])
            )
            db.session.add(new_item)
            db.session.commit()

            return redirect(url_for('inventory.inventory_list'))
        except Exception as e:
            db.session.rollback()
            return render_template('create_inventory_item.html',
                                   error=str(e))

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
        db.session.commit()
        return redirect(url_for('inventory.inventory_list'))

    supplier_email = item.supplier.email if item.supplier else None
    reorder_quantity = item.product.reorder_quantity if item.product else 0
    return render_template('reorder_form.html',
                           item=item,
                           supplier_email=supplier_email,
                           reorder_quantity=reorder_quantity)
