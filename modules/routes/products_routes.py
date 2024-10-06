from flask import Blueprint, render_template, request, redirect, url_for,  jsonify
from modules.inventory.models import Inventory
from modules.products.models import InventoryMovement, Product


from inventory_system import db
import traceback

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def render_product_list():
    products = Product.query.all()
    return render_template('products.html', products=products)

@products_bp.route('/products/<int:product_id>', methods=['GET'])
def product_details(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_details.html', product=product)

@products_bp.route('/products/create', methods=['GET', 'POST'])
def product_create():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        quantity_in_stock = request.form['quantity_in_stock']
        reorder_point = request.form['reorder_point']

        new_product = Product(
            name=name,
            description=description,
            price=price,
            quantity_in_stock=quantity_in_stock,
            reorder_point=reorder_point
        )
        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('products.render_product_list'))

    return render_template('create_product.html')

@products_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = request.form['price']
        product.quantity_in_stock = request.form['quantity_in_stock']
        db.session.commit()
        return redirect(url_for('products.render_product_list'))

    return render_template('edit_product.html', product=product)


@products_bp.route('/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.sales:
        # Render an error page instead of returning JSON
        return render_template(
            'error.html',
            message="Cannot delete a product with associated sales records.")

    # Soft delete by marking product as inactive
    product.is_active = False
    db.session.commit()

    return redirect(url_for('products.view_products'))

@products_bp.route('/products/search', methods=['GET'])
def product_search():
    name = request.args.get('name')
    query = Product.query

    if name:
        query = query.filter(Product.name.ilike(f'%{name}%'))

    products = query.all()

    return render_template('products.html', products=products)
