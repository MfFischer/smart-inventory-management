from flask import Blueprint, render_template, session, redirect, url_for, request
from flask_jwt_extended import create_access_token
from modules.products.models import Product
from modules.inventory.models import Inventory
from modules.users.models import User
from modules.suppliers.models import Supplier

main_bp = Blueprint('main', __name__)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and User.verify_hash(password, user.hashed_password):
            access_token = create_access_token(identity={'username': user.username, 'role': user.role})
            session['logged_in'] = True
            session['user_id'] = user.id
            return redirect(url_for('main.dashboard'))
        else:
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    # This now points to the app-level 'home' function
    return redirect(url_for('home'))

@main_bp.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('main.login'))

    product_count = Product.query.count()
    low_inventory_count = Product.query.filter(Product.quantity_in_stock <= Product.reorder_point).count()
    user_count = User.query.count()
    supplier_count = Supplier.query.count()
    inventory_count = Inventory.query.count()

    return render_template(
        'dashboard.html',
        product_count=product_count,
        low_inventory_count=low_inventory_count,
        user_count=user_count,
        supplier_count=supplier_count,
        inventory_count=inventory_count
    )

