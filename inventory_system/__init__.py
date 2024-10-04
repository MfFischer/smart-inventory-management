from flask import (Flask, render_template, request, redirect,
                   url_for, jsonify, session)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required
import os
import logging

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """
    Create and configure the Flask application.
    Initialize the database, JWT, and register the blueprints.
    """
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, '../app/templates')
    app = Flask(__name__, template_folder=template_dir, static_folder='../app/static')
    print("Template directory:", template_dir)

    # Load app configurations
    app.config.from_object('inventory_system.settings')

    # Initialize the database and JWT with the app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)

    # Import models
    from modules.products.models import Product
    from modules.inventory.models import Inventory
    from modules.users.models import User
    from modules.sales.models import Sale
    from modules.suppliers.models import Supplier

    # Import and register blueprints
    from modules.products.views import products_bp
    from modules.suppliers.views import suppliers_bp
    from modules.inventory.views import inventory_bp
    from modules.sales.views import sales_bp
    from modules.users.views import users_bp

    # Register blueprints for different modules
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(sales_bp, url_prefix='/sales')
    app.register_blueprint(users_bp, url_prefix='/users')

    @app.route('/')
    def home():
        """Render the home page."""
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        Handle user login. On POST, validate the username and password.
        Redirect to the dashboard if successful.
        """
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and User.verify_hash(password, user.hashed_password):
                # Set session variables for logged-in user
                session['user_id'] = user.id
                session['logged_in'] = True
                return redirect(url_for('dashboard'))
            else:
                return render_template(
                    'login.html',
                    error="Invalid username or password")
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        """Log out the user and clear the session."""
        session.pop('logged_in', None)
        session.pop('user_id', None)
        return redirect(url_for('home'))

    @app.route('/dashboard')
    def dashboard():
        """Render the dashboard with an overview of key data
        such as products, sales, and users."""
        if not session.get('logged_in'):
            return redirect(url_for('login'))

        # Fetch various counts and lists for the dashboard
        product_count = Product.query.count()
        low_inventory_products = Product.query.filter(
            Product.quantity_in_stock <= Product.reorder_point
        ).all()
        recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()
        user_count = User.query.count()
        supplier_count = Supplier.query.count()
        suppliers = Supplier.query.all()
        inventory_count = Inventory.query.count()
        inventory_items = Inventory.query.all()

        return render_template('dashboard.html',
                               product_count=product_count,
                               low_inventory_products=low_inventory_products,
                               recent_sales=recent_sales,
                               user_count=user_count,
                               supplier_count=supplier_count,
                               suppliers=suppliers,
                               inventory_count=inventory_count,
                               inventory_items=inventory_items)

    @app.route('/inventory')
    def inventory():
        """Display all inventory items."""
        inventory_items = Inventory.query.all()
        return render_template(
            'inventory.html',
            inventory_items=inventory_items)

    @app.route('/products')
    def products():
        """Fetch and display all products."""
        try:
            products = Product.query.all()
            logging.info(f"Number of products fetched: {len(products)}")
            return render_template('products.html', products=products)
        except Exception as e:
            logging.error("Failed to fetch products", exc_info=True)
            return render_template('products.html', error=str(e))

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

    @app.route('/api/sales', methods=['GET'])
    def get_sales():
        """Return all sales records as JSON data."""
        from modules.sales.views import sales_schema
        sales = Sale.query.all()
        result = sales_schema.dump(sales)
        return jsonify(result), 200

    from modules.users.views import role_required

    @app.route('/users_list')
    # @jwt_required()
    # @role_required('admin')
    def users_list():
        """Display the list of all users."""
        users = User.query.all()
        return render_template('user_list.html', users=users)

    @app.route('/supplier_details/<int:supplier_id>', methods=['GET'])
    def supplier_details(supplier_id=None):
        """
        Display the details of a specific supplier.
        If no supplier_id is provided, display all suppliers.
        """
        if supplier_id:
            supplier = Supplier.query.get_or_404(supplier_id)
            return render_template('supplier_details.html', supplier=supplier)
        else:
            suppliers = Supplier.query.all()
            return render_template('supplier_list.html', suppliers=suppliers)

    @app.route('/inventory/low-stock-alerts', methods=['GET'])
    def low_stock_alerts():
        """Display a list of inventory items that are below the reorder threshold."""
        low_stock_items = Inventory.query.filter(
            Inventory.stock_quantity <= Inventory.reorder_threshold).all()
        return render_template(
            'low_stock_alerts.html',
            low_stock_items=low_stock_items)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return render_template('register.html', error="Email is already registered")

            # Hash the password using the generate_hash method
            hashed_password = User.generate_hash(password)

            # Create new user
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password  # Use the hashed password
            )
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))

        return render_template('register.html')

    return app
