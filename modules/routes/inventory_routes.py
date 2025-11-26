from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from modules.products.models import Product, InventoryMovement
from modules.suppliers.models import Supplier
from modules.inventory.models import Inventory
from inventory_system import db
from datetime import datetime
from modules.users.decorators import role_required

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/')
@login_required
@role_required('admin', 'staff')
def inventory_list():
    """Render the inventory page with items specific to the current user."""
    try:
        inventory_items = Inventory.get_user_inventory()
        print("Inventory items:", [item.to_dict() for item in inventory_items])  # Debug print
        return render_template('inventory.html', inventory_items=inventory_items)
    except Exception as e:
        print(f"Error fetching inventory items: {e}")
        return render_template('error.html'), 500


@inventory_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def inventory_create():
    """Render the form to create a new inventory item associated with the current user."""
    if request.method == 'POST':
        try:
            product_id = request.form.get('product_id')
            stock_quantity = request.form.get('stock_quantity', 0)
            reorder_threshold = request.form.get('reorder_threshold', 0)
            unit_price = request.form.get('unit_price', 0.0)
            cost_price = request.form.get('cost_price', 0.0)

            # Handle new product creation if selected
            if product_id == 'new':
                new_product_name = request.form.get('new_product_name')
                new_product_description = request.form.get('new_product_description', '')

                if not new_product_name:
                    flash("Product name is required for new products.", "error")
                    return redirect(url_for('inventory.inventory_create'))

                if not unit_price or not cost_price:
                    flash("Unit price and cost price are required for new products.", "error")
                    return redirect(url_for('inventory.inventory_create'))

                try:
                    unit_price = float(unit_price)
                    cost_price = float(cost_price)
                except ValueError:
                    flash("Invalid price format.", "error")
                    return redirect(url_for('inventory.inventory_create'))

                # Create new product
                new_product = Product(
                    name=new_product_name,
                    description=new_product_description,
                    price=unit_price,
                    cost_price=cost_price,
                    quantity_in_stock=int(stock_quantity),
                    reorder_point=int(reorder_threshold),
                    user_id=current_user.id
                )
                db.session.add(new_product)
                db.session.flush()
                product_id = new_product.product_id

            else:
                product = Product.query.get(product_id)
                if not product:
                    flash("Selected product does not exist.", "error")
                    return redirect(url_for('inventory.inventory_create'))

            # Handle supplier selection or creation
            supplier_id = request.form.get('supplier_id')
            if supplier_id == 'new':
                new_supplier_name = request.form.get('new_supplier_name')
                new_supplier_email = request.form.get('new_supplier_email')
                new_supplier_contact = request.form.get('new_supplier_contact')

                if not new_supplier_name or not new_supplier_email:
                    flash("Supplier name and email are required for new suppliers.", "error")
                    return redirect(url_for('inventory.inventory_create'))

                new_supplier = Supplier(
                    name=new_supplier_name,
                    email=new_supplier_email,  # Required field
                    contact=new_supplier_contact,
                    user_id=current_user.id
                )
                db.session.add(new_supplier)
                db.session.flush()
                supplier_id = new_supplier.id
            elif supplier_id:
                supplier_id = int(supplier_id)

            # Generate SKU for new inventory item
            sku = f"{product_id[:8]}-{datetime.now().strftime('%Y%m%d')}"

            # Create the new inventory item
            new_item = Inventory(
                product_id=product_id,
                supplier_id=supplier_id,
                sku=sku,
                stock_quantity=int(stock_quantity),
                reorder_threshold=int(reorder_threshold),
                unit_price=float(unit_price),
                cost_price=float(cost_price),
                user_id=current_user.id
            )
            db.session.add(new_item)

            # Create inventory movement record
            movement = InventoryMovement(
                product_id=product_id,
                quantity=int(stock_quantity),
                movement_type='initial_stock',
                user_id=current_user.id,
                notes='Initial inventory creation'
            )
            db.session.add(movement)

            db.session.commit()
            flash("Inventory item created successfully.", "success")
            return redirect(url_for('inventory.inventory_list'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating inventory item: {e}", "error")
            print(f"Error creating inventory item: {e}")
            return render_template('create_inventory_item.html',
                                   error=str(e),
                                   products=Product.get_user_products(),
                                   suppliers=Supplier.query.filter_by(user_id=current_user.id).all())

    # GET request - fetch products and suppliers for dropdowns
    products = Product.get_user_products()
    suppliers = Supplier.query.filter_by(user_id=current_user.id).all()
    return render_template('create_inventory_item.html', products=products, suppliers=suppliers)

@inventory_bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def inventory_edit(item_id):
    """Render form to edit an inventory item if the user has access."""
    item = Inventory.query.get_or_404(item_id)

    # Ensure user can only edit their inventory items
    if item.user_id != current_user.id and item.user_id != current_user.parent_id:
        flash("You do not have permission to edit this inventory item.", "error")
        return redirect(url_for('inventory.inventory_list'))

    if request.method == 'POST':
        try:
            item.product_id = request.form['product_id']
            item.supplier_id = request.form['supplier_id']
            item.sku = request.form['sku']
            item.stock_quantity = request.form['stock_quantity']
            item.reorder_threshold = request.form['reorder_threshold']
            item.unit_price = request.form['unit_price']

            db.session.commit()
            flash("Inventory item updated successfully.", "success")
            return redirect(url_for('inventory.inventory_list'))
        except Exception as e:
            db.session.rollback()
            return render_template('edit_inventory.html', error=str(e), item=item)

    products = Product.get_user_products()
    suppliers = Supplier.query.all()
    return render_template('edit_inventory.html', item=item, products=products, suppliers=suppliers)


@inventory_bp.route('/<int:item_id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'staff')
def inventory_delete(item_id):
    """Delete an inventory item if the user has access."""
    item = Inventory.query.get_or_404(item_id)

    # Ensure user can only delete their inventory items
    if item.user_id != current_user.id and item.user_id != current_user.parent_id:
        flash("You do not have permission to delete this inventory item.", "error")
        return redirect(url_for('inventory.inventory_list'))

    db.session.delete(item)
    db.session.commit()
    flash("Inventory item deleted successfully.", "success")
    return redirect(url_for('inventory.inventory_list'))


@inventory_bp.route('/low-stock-alerts')
@login_required
@role_required('admin', 'staff')
def low_stock_alerts():
    """Display low stock alerts for the current user."""
    try:
        low_stock_items = Inventory.get_low_stock_alerts()
        return render_template('low_stock_alerts.html', low_stock_items=low_stock_items)
    except Exception as e:
        print(f"Error fetching low stock alerts: {e}")
        return render_template('error.html'), 500


@inventory_bp.route('/search')
@login_required
@role_required('admin', 'staff')
def inventory_search():
    """Search for inventory items by product name for the current user."""
    search_query = request.args.get('search')
    if search_query:
        inventory_items = Inventory.query.filter(
            Inventory.product.has(name=search_query)
        ).filter_by(user_id=current_user.id if current_user.role == 'owner' else current_user.parent_id).all()
    else:
        inventory_items = Inventory.get_user_inventory()
    return render_template('inventory.html', inventory_items=inventory_items)


@inventory_bp.route('/<int:item_id>/reorder', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def inventory_reorder(item_id):
    """Handle reorder operations for an inventory item if the user has access."""
    item = Inventory.query.get_or_404(item_id)

    # Ensure user can only reorder their inventory items
    if item.user_id != current_user.id and item.user_id != current_user.parent_id:
        flash("You do not have permission to reorder this item.", "error")
        return redirect(url_for('inventory.inventory_list'))

    if request.method == 'POST':
        item.last_reordered_at = datetime.now()
        item.stock_quantity += item.product.reorder_quantity  # Increment stock by reorder quantity
        db.session.commit()
        flash("Item reordered successfully.", "success")
        return redirect(url_for('inventory.inventory_list'))

    supplier_email = item.supplier.email if item.supplier else None
    reorder_quantity = item.product.reorder_quantity if item.product else 0
    return render_template('reorder_form.html', item=item, supplier_email=supplier_email,
                           reorder_quantity=reorder_quantity)


@inventory_bp.route('/product-details/<string:product_id>', methods=['GET'])
@login_required
@role_required('admin', 'staff')
def get_product_details(product_id):
    """Fetch product details by ID if associated with the user."""
    product = Product.query.get(product_id)
    if product and (product.user_id == current_user.id or product.user_id == current_user.parent_id):
        return {
            'success': True,
            'product': {
                'stock_quantity': product.quantity_in_stock,
                'reorder_threshold': product.reorder_point,
                'unit_price': product.price
            }
        }
    else:
        return {'success': False, 'error': 'Product not found or access denied'}, 404


@inventory_bp.route('/inventory/add_by_scan', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def add_inventory_with_scan():
    """Updates inventory quantities for existing products using barcode scanning"""
    if request.method == 'POST':
        barcode = request.form.get('barcode')
        stock_quantity = request.form.get('stock_quantity')
        unit_price = request.form.get('unit_price')
        cost_price = request.form.get('cost_price')
        reorder_threshold = request.form.get('reorder_threshold')
        supplier_id = request.form.get('supplier_id')

        # Validate required fields
        if not all([barcode, stock_quantity]):
            flash('Barcode and stock quantity are required.', 'error')
            return redirect(url_for('inventory.add_inventory_with_scan'))

        try:
            # Find the product by barcode
            product = Product.query.filter_by(barcode=barcode).first()
            if not product:
                flash('Product not found with this barcode.', 'error')
                return redirect(url_for('inventory.add_inventory_with_scan'))

            # Check if inventory already exists for this product
            existing_inventory = Inventory.query.filter_by(
                product_id=product.product_id,
                user_id=current_user.id
            ).first()

            if existing_inventory:
                # Update existing inventory
                existing_inventory.stock_quantity += int(stock_quantity)
                if unit_price:
                    existing_inventory.unit_price = float(unit_price)
                if cost_price:
                    existing_inventory.cost_price = float(cost_price)
                if reorder_threshold:
                    existing_inventory.reorder_threshold = int(reorder_threshold)
                if supplier_id:
                    existing_inventory.supplier_id = int(supplier_id)

                # Create inventory movement record
                movement = InventoryMovement(
                    product_id=product.product_id,
                    quantity=int(stock_quantity),
                    movement_type='stock_add',
                    user_id=current_user.id,
                    notes='Added via barcode scan'
                )
                db.session.add(movement)
            else:
                # Create new inventory record
                new_inventory = Inventory(
                    product_id=product.product_id,
                    user_id=current_user.id,
                    sku=product.sku,
                    stock_quantity=int(stock_quantity),
                    unit_price=float(unit_price) if unit_price else product.price,
                    cost_price=float(cost_price) if cost_price else product.cost_price,
                    reorder_threshold=int(reorder_threshold) if reorder_threshold else product.reorder_point,
                    supplier_id=int(supplier_id) if supplier_id else product.supplier_id
                )
                db.session.add(new_inventory)

                # Create initial inventory movement record
                movement = InventoryMovement(
                    product_id=product.product_id,
                    quantity=int(stock_quantity),
                    movement_type='initial_stock',
                    user_id=current_user.id,
                    notes='Initial stock via barcode scan'
                )
                db.session.add(movement)

            db.session.commit()
            flash('Inventory updated successfully!', 'success')
            return redirect(url_for('inventory.inventory_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating inventory: {str(e)}', 'error')
            return redirect(url_for('inventory.add_inventory_with_scan'))

    # GET request - render the form
    suppliers = Supplier.query.filter_by(user_id=current_user.id).all()
    return render_template('add_inventory_with_scan.html', suppliers=suppliers)


@inventory_bp.route('/api/get_product_by_barcode')
@login_required
@role_required('admin', 'staff')
def get_product_by_barcode():
    barcode = request.args.get('barcode')
    if not barcode:
        return jsonify({'error': 'Barcode is required'}), 400

    try:
        # Find product for current user or their parent
        query = Product.query.filter_by(barcode=barcode)
        if current_user.role == 'staff':
            query = query.filter_by(user_id=current_user.parent_id)
        else:
            query = query.filter_by(user_id=current_user.id)

        product = query.first()

        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Get current inventory
        inventory = Inventory.query.filter_by(product_id=product.product_id).first()
        current_stock = inventory.stock_quantity if inventory else 0

        return jsonify({
            'product_id': product.product_id,
            'name': product.name,
            'sku': product.sku,
            'current_stock': current_stock,
            'unit_price': str(product.price),  # Convert Decimal to string
            'cost_price': str(product.cost_price),
            'reorder_point': product.reorder_point,
            'supplier_id': product.supplier_id
        })

    except Exception as e:
        print(f"Error in get_product_by_barcode: {str(e)}")  # Add server-side logging
        return jsonify({'error': 'Internal server error'}), 500