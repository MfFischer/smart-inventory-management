from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required
from modules.products.models import InventoryMovement, Product
from modules.suppliers.models import Supplier
from modules.inventory.models import Inventory
from inventory_system import db
from modules.users.decorators import role_required

products_bp = Blueprint('products', __name__)

@products_bp.route('/', methods=['GET'])
@login_required
def render_product_list():
    if current_user.role == 'admin' or current_user.role == 'owner':
        # Admins and owners see their own products
        products = Product.query.filter_by(user_id=current_user.id).all()
    elif current_user.role == 'staff':
        # Staff see products belonging to their parent admin/owner
        products = Product.query.filter_by(user_id=current_user.parent_id).all()
    else:
        products = []  # Default to empty if the role is not recognized

    return render_template('products.html', products=products)

@products_bp.route('/products/details/<string:product_id>', methods=['GET'])
@login_required
@role_required('admin', 'staff')
def product_details(product_id):
    product = Product.query.get_or_404(product_id)
    # Ensure user can only view their products
    if product.user_id != current_user.id and product.user_id != current_user.parent_id:
        flash("You do not have access to this product.", "error")
        return redirect(url_for('products.render_product_list'))
    return render_template('product_details.html', product=product)

@products_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def product_create():
    if request.method == 'POST':
        try:
            # Collect form data with defaults for required fields
            name = request.form.get('name')
            description = request.form.get('description', '')
            price = request.form.get('price')
            cost_price = request.form.get('cost_price')
            quantity_in_stock = request.form.get('quantity_in_stock', '0')
            reorder_point = request.form.get('reorder_point', '0')
            reorder_quantity = request.form.get('reorder_quantity', '0')
            barcode = request.form.get('barcode')
            supplier_id = request.form.get('supplier_id')

            # Validate required fields
            if not all([name, price, cost_price]):
                flash('Name, price, and cost price are required fields', 'error')
                return redirect(url_for('products.product_create'))

            # Handle new supplier creation
            if supplier_id == 'new':
                new_supplier_name = request.form.get('new_supplier_name')
                new_supplier_email = request.form.get('new_supplier_email')
                new_supplier_contact = request.form.get('new_supplier_contact')

                if not new_supplier_name or not new_supplier_email:
                    flash('Supplier name and email are required when adding a new supplier', 'error')
                    return redirect(url_for('products.product_create'))

                new_supplier = Supplier(
                    name=new_supplier_name,
                    email=new_supplier_email,
                    contact=new_supplier_contact,
                    user_id=current_user.id
                )
                db.session.add(new_supplier)
                db.session.flush()
                supplier_id = new_supplier.id
            elif supplier_id:
                supplier_id = int(supplier_id)

            # Convert string values to appropriate types
            try:
                price = float(price)
                cost_price = float(cost_price)
                quantity_in_stock = int(quantity_in_stock)
                reorder_point = int(reorder_point)
                reorder_quantity = int(reorder_quantity)
            except (ValueError, TypeError) as e:
                flash(f'Invalid number format: {str(e)}', 'error')
                return redirect(url_for('products.product_create'))

            # Create new product
            new_product = Product(
                name=name,
                description=description,
                price=price,
                cost_price=cost_price,
                quantity_in_stock=quantity_in_stock,
                barcode=barcode if barcode else None,
                reorder_point=reorder_point,
                reorder_quantity=reorder_quantity,
                supplier_id=supplier_id,
                user_id=current_user.id
            )

            db.session.add(new_product)
            db.session.flush()

            # Generate SKU
            sku = Product.generate_sku(name)

            # Create inventory record
            inventory_item = Inventory(
                product_id=new_product.product_id,
                user_id=current_user.id,
                sku=sku,
                stock_quantity=quantity_in_stock,
                reorder_threshold=reorder_point,
                unit_price=price,
                cost_price=cost_price,
                supplier_id=supplier_id
            )

            # Create initial inventory movement record
            movement = InventoryMovement(
                product_id=new_product.product_id,
                quantity=quantity_in_stock,
                movement_type='initial_stock',
                user_id=current_user.id,
                notes='Initial stock on product creation'
            )

            db.session.add(inventory_item)
            db.session.add(movement)
            db.session.commit()

            flash('Product created successfully!', 'success')
            return redirect(url_for('products.render_product_list'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating product: {str(e)}")
            flash(f'Error creating product: {str(e)}', 'error')
            return redirect(url_for('products.product_create'))

    # GET request - render the form
    suppliers = Supplier.query.filter_by(user_id=current_user.id).all()
    return render_template('create_product.html', suppliers=suppliers)

@products_bp.route('/products/edit/<string:product_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)

    # Ensure user can only edit their products
    if product.user_id != current_user.id and product.user_id != current_user.parent_id:
        flash("You do not have permission to edit this product.", "error")
        return redirect(url_for('products.render_product_list'))

    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = request.form['price']
        product.quantity_in_stock = request.form['quantity_in_stock']
        product.reorder_point = request.form['reorder_point']
        product.reorder_quantity = request.form['reorder_quantity']

        # Commit the changes to the database
        try:
            db.session.commit()
            flash("Product updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating product: {e}", "error")

        return redirect(url_for('products.render_product_list'))

    return render_template('edit_product.html', product=product)

@products_bp.route('/products/<string:product_id>', methods=['GET'])
@login_required
@role_required('admin', 'staff')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    # Ensure user can only delete their products
    if product.user_id != current_user.id and product.user_id != current_user.parent_id:
        flash("You do not have permission to delete this product.", "error")
        return redirect(url_for('products.render_product_list'))

    if product.sales:
        # Render an error page instead of returning JSON
        return render_template(
            'error.html',
            message="Cannot delete a product with associated sales records.")

    # Soft delete by marking product as inactive
    product.is_active = False
    db.session.commit()

    flash("Product deleted successfully.", "success")
    return redirect(url_for('products.render_product_list'))

@products_bp.route('/products/search', methods=['GET'])
@login_required
@role_required('admin', 'staff')
def product_search():
    name = request.args.get('name')
    query = Product.query

    if name:
        query = query.filter(Product.name.ilike(f'%{name}%'))

    # Restrict search to products associated with the current user
    if current_user.role == 'owner':
        query = query.filter_by(user_id=current_user.id)
    else:
        query = query.filter_by(user_id=current_user.parent_id)

    products = query.all()

    return render_template('products.html', products=products)


@products_bp.route('/add_product_with_scan', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def add_product_with_scan():
    """Creates a new product entry using barcode scanning"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            cost_price = request.form.get('cost_price')
            quantity_in_stock = request.form.get('quantity_in_stock', 0)
            barcode = request.form.get('barcode')
            reorder_point = request.form.get('reorder_point', 0)
            supplier_id = request.form.get('supplier_id')

            # Validate required fields
            if not all([name, price, cost_price]):
                flash('Name, price, and cost price are required fields.', 'error')
                return redirect(url_for('products.add_product_with_scan'))

            # Convert string values to appropriate types
            try:
                price = float(price)
                cost_price = float(cost_price)
                quantity_in_stock = int(quantity_in_stock)
                reorder_point = int(reorder_point)
                supplier_id = int(supplier_id) if supplier_id else None
            except ValueError as e:
                flash(f'Invalid number format: {str(e)}', 'error')
                return redirect(url_for('products.add_product_with_scan'))

            # Create new product
            new_product = Product(
                name=name,
                description=description,
                price=price,
                cost_price=cost_price,
                quantity_in_stock=quantity_in_stock,
                barcode=barcode,
                reorder_point=reorder_point,
                reorder_quantity=0,
                user_id=current_user.id,
                supplier_id=supplier_id
            )
            db.session.add(new_product)
            db.session.flush()

            # Create inventory record
            inventory_item = Inventory(
                product_id=new_product.product_id,
                user_id=current_user.id,
                sku=Product.generate_sku(name),
                stock_quantity=quantity_in_stock,
                unit_price=price,
                cost_price=cost_price,
                reorder_threshold=reorder_point,
                supplier_id=supplier_id
            )
            db.session.add(inventory_item)
            db.session.commit()

            flash('Product added successfully!', 'success')
            return redirect(url_for('products.render_product_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating product: {str(e)}', 'error')
            return redirect(url_for('products.add_product_with_scan'))

    # GET request - render the form
    suppliers = Supplier.query.filter_by(user_id=current_user.id).all()
    return render_template('add_product_with_scan.html', suppliers=suppliers)