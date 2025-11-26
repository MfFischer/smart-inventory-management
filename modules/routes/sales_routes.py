from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_required
from inventory_system import db
from modules.sales.models import Sale, SaleItem
from modules.products.models import Product
from decimal import Decimal
from modules.inventory.models import Inventory
from modules.business.models import Business
from datetime import datetime
from flask import jsonify
from urllib.parse import unquote

sales_bp = Blueprint('sales', __name__)


@sales_bp.route('/')
@login_required
def sale_list():
    """Render the sales page with user-specific sales and search functionality."""
    # Get search parameters
    search = request.args.get('search', '').strip()
    search_type = request.args.get('search_type', 'receipt')

    # Base query
    if current_user.role == 'admin':
        query = Sale.query.filter(
            (Sale.user_id == current_user.id) |
            (Sale.user_id.in_([child.id for child in current_user.children]))
        )
    else:
        query = Sale.query.filter_by(user_id=current_user.id)

    # Apply search if provided
    if search:
        if search_type == 'receipt':
            query = query.filter(Sale.receipt_number.ilike(f'%{search}%'))
        elif search_type == 'customer':
            query = query.filter(Sale.customer_name.ilike(f'%{search}%'))
        elif search_type == 'date':
            try:
                search_date = datetime.strptime(search, '%Y-%m-%d').date()
                query = query.filter(db.func.date(Sale.created_at) == search_date)
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", "error")

    # Order by most recent first
    sales = query.order_by(Sale.created_at.desc()).all()

    if not sales and search:
        flash(f"No sales found matching your search.", "info")

    return render_template('sales.html', sales=sales)

@sales_bp.route('/<int:sale_id>')
@login_required
def sale_details(sale_id):
    """Render detailed information of a sale by ID if user has access."""
    # Use joinedload to eagerly load the relationships
    sale = Sale.query.options(
        db.joinedload(Sale.sale_items)
        .joinedload(SaleItem.product)
    ).get_or_404(sale_id)

    # Ensure user can only view their sales
    if sale.user_id != current_user.id and sale.user_id != current_user.parent_id:
        flash("You do not have permission to view this sale.", "error")
        return redirect(url_for('sales.sale_list'))

    # Debug print to verify data
    print(f"Sale ID: {sale.id}")
    print(f"Sale Items: {len(sale.sale_items)}")
    for item in sale.sale_items:
        print(f"Product: {item.product.name}, Cost Price: {item.product.cost_price}")

    return render_template('sale_details.html', sale=sale)


@sales_bp.route('/add', methods=['GET', 'POST'])
@login_required
def sale_create():
    """Unified sale creation route handling both manual and barcode scanning."""
    if request.method == 'POST':
        # Your existing POST handling code remains the same
        try:
            product_ids = request.form.getlist('product_ids[]')
            quantities = request.form.getlist('quantities[]')
            discount_percentages = request.form.getlist('discount_percentages[]')
            customer_name = request.form.get('customer_name', "Anonymous Customer")
            sale_status = request.form.get('sale_status', 'completed')

            # Initialize variables for sale calculations
            sale_items = []
            total_price = Decimal(0)
            total_cost = Decimal(0)

            for idx, product_id in enumerate(product_ids):
                product = Product.query.get(product_id)
                if not product:
                    flash(f"Product with ID {product_id} not found.", "error")
                    continue

                # Validate quantity input
                try:
                    quantity = Decimal(int(quantities[idx]))
                except (ValueError, IndexError):
                    flash(f"Invalid quantity for product {product.name}.", "error")
                    continue

                # Validate discount percentage input
                try:
                    discount_percentage = Decimal(float(discount_percentages[idx]))
                except (ValueError, IndexError):
                    flash(f"Invalid discount percentage for product {product.name}.", "error")
                    continue

                if product.quantity_in_stock < quantity:
                    flash(f"Insufficient stock for product {product.name}.", "error")
                    continue

                price_per_unit = Decimal(product.price)
                cost_price = Decimal(product.cost_price)

                # Apply discount
                discount_factor = Decimal(1) - (discount_percentage / Decimal(100))
                item_total = price_per_unit * quantity * discount_factor
                total_price += item_total
                total_cost += cost_price * quantity

                sale_item = SaleItem(
                    product_id=product_id,
                    quantity=int(quantity),
                    price_per_unit=price_per_unit,
                    discount_percentage=float(discount_percentage)
                )
                sale_items.append(sale_item)

                # Deduct stock from the product
                product.quantity_in_stock -= int(quantity)

                # Deduct stock from the corresponding inventory item
                inventory_item = Inventory.query.filter_by(product_id=product_id).first()
                if inventory_item:
                    if inventory_item.stock_quantity >= int(quantity):
                        inventory_item.stock_quantity -= int(quantity)
                    else:
                        flash(f"Insufficient inventory for product {product.name}.", "error")
                        continue

            if not sale_items:
                flash("No valid sale items to process.", "warning")
                return redirect(url_for('sales.sale_create'))

            # Create a new Sale instance
            sale = Sale(
                customer_name=customer_name,
                sale_status=sale_status,
                user_id=current_user.id,
                sale_items=sale_items,
                total_price=total_price,
                profit=total_price - total_cost
            )

            # Add and commit the new sale to the database
            db.session.add(sale)
            db.session.commit()
            flash("Sale(s) added successfully.", "success")
            return redirect(url_for('sales.sale_list'))

        except Exception as e:
            db.session.rollback()
            print("An unexpected error occurred:", e)
            flash(f"An unexpected error occurred: {e}", "error")
            return redirect(url_for('sales.sale_create'))

    products = Product.get_user_products()
    return render_template('add_sale.html', products=products)


@sales_bp.route('/get-product-by-barcode/<string:barcode>', methods=['GET'])
@login_required
def get_product_by_barcode(barcode):
    """API endpoint to get product details from barcode."""
    try:
        # Clean and decode the barcode
        barcode = unquote(barcode).strip()
        current_app.logger.debug(f"Received barcode request: {barcode}")

        # Find product specific to the user
        product = Product.query.filter(
            Product.barcode == barcode,
            (Product.user_id == current_user.id) |
            (Product.user_id == current_user.parent_id)
        ).first()

        if not product:
            current_app.logger.warning(f"No product found for barcode: {barcode}")
            return jsonify({
                'success': False,
                'error': 'Product not found'
            }), 404

        current_app.logger.info(f"Found product {product.name} for barcode {barcode}")

        # Return product data
        return jsonify({
            'success': True,
            'product': {
                'product_id': str(product.product_id),  # Convert UUID to string
                'name': product.name,
                'barcode': product.barcode,
                'price': str(product.price),
                'cost_price': str(product.cost_price),
                'quantity_in_stock': product.quantity_in_stock
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error processing barcode {barcode}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@sales_bp.route('/<int:sale_id>/edit', methods=['GET', 'POST'])
@login_required
def sale_edit(sale_id):
    """Render the form to edit a sale if the user has access."""
    sale = Sale.query.get_or_404(sale_id)

    # Ensure user can only edit their sales
    if sale.user_id != current_user.id and sale.user_id != current_user.parent_id:
        flash("You do not have permission to edit this sale.", "error")
        return redirect(url_for('sales.sale_list'))

    if request.method == 'POST':
        try:
            # Update sale details
            sale.sale_status = request.form['sale_status']
            sale.customer_name = request.form.get('customer_name', sale.customer_name)

            db.session.commit()
            flash("Sale updated successfully.", "success")
            return redirect(url_for('sales.sale_list'))

        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected error occurred: {e}", "error")
            return redirect(url_for('sales.sale_edit', sale_id=sale_id))

    return render_template('edit_sale.html', sale=sale)


@sales_bp.route('/<int:sale_id>/delete', methods=['POST'])
@login_required
def sale_delete(sale_id):
    """Delete a sale by ID if the user has access."""
    sale = Sale.query.get_or_404(sale_id)

    # Ensure user can only delete their sales
    if sale.user_id != current_user.id and sale.user_id != current_user.parent_id:
        flash("You do not have permission to delete this sale.", "error")
        return redirect(url_for('sales.sale_list'))

    db.session.delete(sale)
    db.session.commit()
    flash("Sale deleted successfully.", "success")
    return redirect(url_for('sales.sale_list'))


@sales_bp.route('/search')
@login_required
def sale_search():
    """Search user-specific sales by date or other criteria."""
    query = Sale.get_user_sales()
    date = request.args.get('date')

    if date:
        query = query.filter(Sale.created_at.like(f"%{date}%"))

    sales = query.all()
    return render_template('sales.html', sales=sales)


@sales_bp.route('/receipt/<int:sale_id>')
@login_required
def sale_receipt(sale_id):
    """Generate a printable receipt for a sale."""
    sale = Sale.query.options(
        db.joinedload(Sale.sale_items)
        .joinedload(SaleItem.product)
    ).get_or_404(sale_id)

    if sale.user_id != current_user.id and sale.user_id != current_user.parent_id:
        flash("You do not have permission to view this receipt.", "error")
        return redirect(url_for('sales.sale_list'))

    business = Business.query.filter_by(user_id=current_user.id).first()

    return render_template('receipt.html',
                           sale=sale,
                           business=business,
                           Decimal=Decimal)  # Pass Decimal class to template


@sales_bp.route('/pending')
@login_required
def get_pending_sale():
    """Get the current user's pending sale."""
    sale = Sale.query.filter_by(
        user_id=current_user.id,
        sale_status='pending'
    ).first()

    if not sale:
        return jsonify({'sale': None})

    return jsonify({'sale': sale.to_dict()})


@sales_bp.route('/complete-sale/<int:sale_id>', methods=['POST'])
@login_required
def complete_sale():
    """Complete a pending sale."""
    try:
        data = request.get_json()
        sale_id = data.get('sale_id')
        customer_name = data.get('customer_name', 'Anonymous Customer')

        sale = Sale.query.get_or_404(sale_id)

        if sale.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        sale.sale_status = 'completed'
        sale.customer_name = customer_name
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Sale completed successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@sales_bp.route('/scan', methods=['POST'])
@login_required
def scan_barcode():
    try:
        data = request.get_json()
        barcode = data.get('barcode')
        quantity = data.get('quantity', 1)

        # Find product by barcode
        product = Product.query.filter_by(barcode=barcode).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Get or create pending sale
        sale = Sale.query.filter_by(
            user_id=current_user.id,
            sale_status='pending'
        ).first()

        if not sale:
            sale = Sale(
                user_id=current_user.id,
                sale_status='pending',
                customer_name='Pending Customer'
            )
            db.session.add(sale)

        # Add item to sale
        sale_item = SaleItem(
            product_id=product.id,
            quantity=quantity,
            price_per_unit=product.price
        )
        sale.sale_items.append(sale_item)

        # Calculate total
        sale.total_price = sum(item.price_per_unit * item.quantity for item in sale.sale_items)

        db.session.commit()

        return jsonify({
            'sale': {
                'id': sale.id,
                'total_price': float(sale.total_price),
                'sale_items': [{
                    'id': item.id,
                    'product': {
                        'name': item.product.name,
                        'price': float(item.price_per_unit)
                    },
                    'quantity': item.quantity,
                    'price_per_unit': float(item.price_per_unit)
                } for item in sale.sale_items]
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@sales_bp.route('/update-item/<int:item_id>', methods=['POST'])
@login_required
def update_sale_item(item_id):
    try:
        data = request.get_json()
        quantity = data.get('quantity')

        sale_item = SaleItem.query.get_or_404(item_id)
        sale = sale_item.sale

        if sale.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        sale_item.quantity = quantity
        sale.total_price = sum(item.price_per_unit * item.quantity for item in sale.sale_items)

        db.session.commit()

        return jsonify({'sale': sale.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@sales_bp.route('/remove-item/<int:item_id>', methods=['POST'])
@login_required
def remove_sale_item(item_id):
    try:
        sale_item = SaleItem.query.get_or_404(item_id)
        sale = sale_item.sale

        if sale.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403

        db.session.delete(sale_item)

        if not sale.sale_items:
            db.session.delete(sale)
            db.session.commit()
            return jsonify({'sale': None})

        sale.total_price = sum(item.price_per_unit * item.quantity for item in sale.sale_items)
        db.session.commit()

        return jsonify({'sale': sale.to_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@sales_bp.route('/receipt/search', methods=['GET', 'POST'])
@login_required
def search_receipt():
    """Search for sales receipts by date range, customer name, or receipt number."""
    try:
        if request.method == 'POST':
            # Get search parameters
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            customer_name = request.form.get('customer_name')
            receipt_number = request.form.get('receipt_number')

            # Start with base query for user's sales
            query = Sale.query

            # Filter by user access
            if current_user.role == 'admin':
                query = query.filter(
                    (Sale.user_id == current_user.id) |
                    (Sale.user_id.in_([child.id for child in current_user.children]))
                )
            else:
                query = query.filter_by(user_id=current_user.id)

            # Apply filters based on search criteria
            if start_date and end_date:
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    end = datetime.strptime(end_date, '%Y-%m-%d')
                    end = end.replace(hour=23, minute=59, second=59)  # Include full end date
                    query = query.filter(Sale.created_at.between(start, end))
                except ValueError:
                    flash('Invalid date format', 'error')

            if customer_name:
                query = query.filter(Sale.customer_name.ilike(f'%{customer_name}%'))

            if receipt_number:
                query = query.filter(Sale.receipt_number.ilike(f'%{receipt_number}%'))

            # Execute query and get results
            sales = query.order_by(Sale.created_at.desc()).all()

            # Flash message about results
            if not sales:
                flash('No receipts found matching your criteria', 'info')
            else:
                flash(f'Found {len(sales)} matching receipt(s)', 'success')

            return render_template('search_receipt.html', sales=sales)

        # GET request - show empty form
        return render_template('search_receipt.html', sales=None)

    except Exception as e:
        flash(f'An error occurred while searching: {str(e)}', 'error')
        return render_template('search_receipt.html', sales=None)
