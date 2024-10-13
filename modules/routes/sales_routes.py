from flask import Blueprint, render_template, request, redirect, url_for
from inventory_system import db
from modules.sales.models import Sale
from modules.products.models import Product

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/')
def sale_list():
    """Render the sales page with optional search by date."""
    search_date = request.args.get('date')
    if search_date:
        sales = Sale.query.filter(db.func.date(Sale.created_at) == search_date).all()
    else:
        sales = Sale.query.all()
    return render_template('sales.html', sales=sales)

@sales_bp.route('/<int:sale_id>')
def sale_details(sale_id):
    """Render the details of a sale by ID (HTML)."""
    sale = Sale.query.get_or_404(sale_id)
    return render_template('sale_details.html', sale=sale)

@sales_bp.route('/add', methods=['GET', 'POST'])
def sale_create():
    """Render the form to add a new sale."""
    if request.method == 'POST':
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])

        product = Product.query.get(product_id)
        if not product:
            return "Product not found", 404

        if product.quantity_in_stock < quantity:
            return "Insufficient stock to fulfill sale", 400  # Or render an error message on the template

        total_price = product.price * quantity
        new_sale = Sale(
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
            sale_status=request.form.get('sale_status', 'completed')
        )
        db.session.add(new_sale)
        product.quantity_in_stock -= quantity  # Deduct quantity
        db.session.commit()  # Commit both the new sale and updated product stock

        return redirect(url_for('sales.sale_list'))

    products = Product.query.all()
    return render_template('add_sale.html', products=products)

@sales_bp.route('/<int:sale_id>/edit', methods=['GET', 'POST'])
def sale_edit(sale_id):
    """Render the form to edit a sale."""
    sale = Sale.query.get_or_404(sale_id)

    if request.method == 'POST':
        quantity = int(request.form['quantity'])

        product = Product.query.get(sale.product_id)
        if not product:
            return "Product not found", 404

        total_price = product.price * quantity
        sale.quantity = quantity
        sale.total_price = total_price
        sale.sale_status = request.form['sale_status']

        db.session.commit()

        return redirect(url_for('sales.sale_list'))

    return render_template('edit_sale.html', sale=sale)

@sales_bp.route('/<int:sale_id>/delete', methods=['POST'])
def sale_delete(sale_id):
    """Delete a sale by ID (HTML form-based)."""
    sale = Sale.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    return redirect(url_for('sales.sale_list'))

@sales_bp.route('/search')
def sale_search():
    """Search sales by date or other criteria."""
    query = Sale.query
    date = request.args.get('date')

    if date:
        query = query.filter(Sale.created_at.like(f"%{date}%"))

    sales = query.all()
    return render_template('sales.html', sales=sales)
