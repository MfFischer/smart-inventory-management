from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os
from flask import session
import logging

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, '../app/templates')
    app = Flask(__name__, template_folder=template_dir, static_folder='../app/static')
    print("Template directory:", template_dir)

    app.config.from_object('inventory_system.settings')

    # Initialize the database and JWT with the app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt = JWTManager(app)

    # Import models
    from modules.products.models import Product
    from modules.inventory.models import Inventory
    from modules.users.models import User  # Assuming User model exists

    # Import and register blueprints
    from modules.products.views import products_bp
    from modules.suppliers.views import suppliers_bp
    from modules.inventory.views import inventory_bp
    from modules.sales.views import sales_bp
    from modules.users.views import users_bp

    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(sales_bp, url_prefix='/api/sales')
    app.register_blueprint(users_bp, url_prefix='/api/users')

    @app.route('/')
    def home():
        print("Template directory:", os.path.abspath(app.template_folder))  # Debugging line
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            if user and User.verify_hash(password, user.hashed_password):
                session['user_id'] = user.id  # Set user_id in session
                session['logged_in'] = True  # Mark the user as logged in
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Invalid username or password")
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        # Clear the user session
        session.pop('logged_in', None)
        session.pop('user_id', None)
        return redirect(url_for('home'))

    @app.route('/dashboard')
    def dashboard():
        if not session.get('logged_in'):
            return redirect(url_for('login'))

        # Importing Sale locally to avoid circular import
        from modules.sales.models import Sale

        # Fetch data needed for the dashboard
        product_count = Product.query.count()
        low_inventory_products = Product.query.filter(Product.quantity_in_stock <= Product.reorder_point).all()
        recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()  # Get the last 5 sales records

        return render_template('dashboard.html', product_count=product_count,
                               low_inventory_products=low_inventory_products,
                               recent_sales=recent_sales)

    @app.route('/inventory')
    def inventory():
        # Ensure you have an Inventory model
        inventory_items = Inventory.query.all()
        # Pass the data to the template
        return render_template('inventory.html',
                               inventory_items=inventory_items)

    @app.route('/products')
    def products():
        try:
            products = Product.query.all()
            logging.info(f"Number of products fetched: {len(products)}")
            return render_template('products.html', products=products)
        except Exception as e:
            logging.error("Failed to fetch products", exc_info=True)
            return render_template('products.html', error=str(e))

    @app.route('/add-product', methods=['GET', 'POST'])
    def add_product():
        if request.method == 'POST':
            new_product = Product(
                name=request.form['name'],
                description=request.form['description'],
                price=request.form['price'],
                reorder_point=request.form['reorder_point']
            )
            db.session.add(new_product)
            db.session.commit()
            # Redirect to dashboard after adding
            return redirect(url_for('dashboard'))
        return render_template('add_product.html')

    return app
