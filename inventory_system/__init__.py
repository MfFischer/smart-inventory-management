from flask import (Flask, render_template, request, redirect, url_for, jsonify, session)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_restx import Api  # Import Flask-RESTX Api
import os
import logging
from .swagger import init_swagger  # Import Swagger initializer

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """
    Create and configure the Flask application.
    Initialize the database, JWT, and register the namespaces for APIs.
    """
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, '../app/templates')
    app = Flask(__name__, template_folder=template_dir, static_folder='../app/static')

    # Load app configurations
    app.config.from_object('inventory_system.settings')

    # Initialize the database and JWT with the app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)

    # Initialize Flask-RESTX API
    api = Api(app, title="Smart Inventory System API", version="1.0",
              description="API for managing inventory, products, sales, and users.")

    # Import models
    from modules.products.models import Product
    from modules.inventory.models import Inventory
    from modules.users.models import User
    from modules.sales.models import Sale
    from modules.suppliers.models import Supplier

    # Import and register namespaces for different modules (using Flask-RESTX)
    from modules.products.views import api as products_ns
    from modules.suppliers.views import api as suppliers_ns
    from modules.inventory.views import api as inventory_ns
    from modules.sales.views import api as sales_ns
    from modules.users.views import api as users_ns

    # Add namespaces to the API
    api.add_namespace(products_ns, path='/api/products')
    api.add_namespace(suppliers_ns, path='/api/suppliers')
    api.add_namespace(inventory_ns, path='/api/inventory')
    api.add_namespace(sales_ns, path='/api/sales')
    api.add_namespace(users_ns, path='/api/users')

    # Initialize Swagger documentation
    init_swagger(app)

    # Routes for templates and static pages
    @app.route('/')
    def home():
        """Render the home page."""
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Handle user login."""
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and User.verify_hash(password, user.hashed_password):
                session['user_id'] = user.id
                session['logged_in'] = True
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Invalid username or password")
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        """Log out the user and clear the session."""
        session.pop('logged_in', None)
        session.pop('user_id', None)
        return redirect(url_for('home'))

    @app.route('/dashboard')
    def dashboard():
        """Render the dashboard with an overview of key data."""
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        product_count = Product.query.count()
        low_inventory_products = Product.query.filter(Product.quantity_in_stock <= Product.reorder_point).all()
        recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()
        user_count = User.query.count()
        supplier_count = Supplier.query.count()
        inventory_count = Inventory.query.count()

        return render_template(
            'dashboard.html',
            product_count=product_count,
            low_inventory_products=low_inventory_products,
            recent_sales=recent_sales,
            user_count=user_count,
            supplier_count=supplier_count,
            inventory_count=inventory_count
        )

    @app.route('/inventory')
    def inventory():
        """Display all inventory items."""
        inventory_items = Inventory.query.all()
        return render_template('inventory.html', inventory_items=inventory_items)

    @app.route('/products')
    def products():
        """Fetch and display all products."""
        products = Product.query.all()
        return render_template('products.html', products=products)

    @app.route('/add-product', methods=['GET', 'POST'])
    def add_product():
        """Add a new product to the database."""
        if request.method == 'POST':
            new_product = Product(
                name=request.form['name'],
                description=request.form['description'],
                price=request.form['price'],
                reorder_point=request.form['reorder_point']
            )
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for('dashboard'))
        return render_template('add_product.html')

    @app.route('/sales', methods=['GET'])
    def view_sales():
        """Render the sales page to view all sales records."""
        sales = Sale.query.all()
        return render_template('sales.html', sales=sales)

    @app.route('/users_list')
    def users_list():
        """Display the list of all users."""
        users = User.query.all()
        return render_template('user_list.html', users=users)

    @app.route('/supplier_details/<int:supplier_id>', methods=['GET'])
    def supplier_details(supplier_id=None):
        """Display the details of a specific supplier."""
        supplier = Supplier.query.get_or_404(supplier_id) if supplier_id else Supplier.query.all()
        return render_template('supplier_details.html', supplier=supplier)

    @app.route('/inventory/low-stock-alerts', methods=['GET'])
    def low_stock_alerts():
        """Display a list of inventory items below the reorder threshold."""
        low_stock_items = Inventory.query.filter(Inventory.stock_quantity <= Inventory.reorder_threshold).all()
        return render_template('low_stock_alerts.html', low_stock_items=low_stock_items)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Handle user registration."""
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return render_template('register.html', error="Email is already registered")
            hashed_password = User.generate_hash(password)
            new_user = User(username=username, email=email, hashed_password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        return render_template('register.html')

    return app
