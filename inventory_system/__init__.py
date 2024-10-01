from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask import Flask, render_template, request, redirect, url_for
import os

# Initialize SQLAlchemy and Flask-Migrate instances
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """
    Factory function to create and configure the Flask application.
    """
    # Create Flask app instance
    app = Flask(__name__, template_folder="../templates")

    # Load configuration settings from settings.py
    app.config.from_object('inventory_system.settings')

    # Initialize the database and migration tools with the app
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize JWT Manager
    jwt = JWTManager(app)

    # Import and register blueprints for different modules
    from products.views import products_bp
    from suppliers.views import suppliers_bp
    from inventory.views import inventory_bp
    from sales.views import sales_bp
    from users.views import users_bp

    # Register blueprints with the app
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(sales_bp, url_prefix='/api/sales')
    app.register_blueprint(users_bp, url_prefix='/api/users')

    # Define root route
    @app.route('/')
    def home():
        print("Template path:", os.path.join(app.template_folder, 'index.html'))
        return render_template('index.html')

    # Add product route
    @app.route('/add-product', methods=['GET', 'POST'])
    def add_product():
        from products.models import Product

        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            reorder_point = request.form['reorder_point']

            # Create new product
            new_product = Product(name=name, description=description, price=price, reorder_point=reorder_point)
            db.session.add(new_product)
            db.session.commit()

            return redirect(url_for('home'))

        return render_template('add_product.html')

    # Search product route
    @app.route('/search-product', methods=['GET'])
    def search_product():
        from products.models import Product

        # Get the product name from the search form
        name = request.args.get('name')

        # Query the database for products matching the name
        products = Product.query.filter(Product.name.ilike(f'%{name}%')).all()

        # Render the search template and pass the products as context
        return render_template('search.html', products=products)

    return app
