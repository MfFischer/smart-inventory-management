from flask import request, jsonify, render_template, redirect, url_for
from flask_restx import Namespace, Resource
from modules.products.models import Product
from modules.products.serializers import ProductSchema
from inventory_system import db
from sqlalchemy.exc import SQLAlchemyError

# Define a namespace for the products API (JSON responses only)
api = Namespace('products_api', description='Products API operations')

# Initialize the ProductSchema for validation
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# ------------------------------
# HTML Routes: Move to separate Blueprint or handle directly in main_bp
# ------------------------------

# Class-based resource for rendering all products (HTML view)
@api.route('/html/product_list')
class ProductListHTML(Resource):
    def get(self):
        """Render all products for the HTML view."""
        products = Product.query.all()
        return render_template('products.html', products=products)

# Class-based resource for handling product details (HTML view)
@api.route('/html/<int:product_id>')
class ProductDetailsHTML(Resource):
    def get(self, product_id):
        """Get a product by ID and render the product details page (HTML)."""
        product = Product.query.get_or_404(product_id)
        return render_template('product_details.html', product=product)

# Class-based resource for rendering and handling the create product form
@api.route('/html/create')
class ProductCreateHTML(Resource):
    def get(self):
        """Render the create product form."""
        return render_template('create_product.html')

    def post(self):
        """Handle the form submission to create a new product."""
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

        return redirect(url_for('main.product_list'))  # Change this to reflect the actual route

# Class-based resource for editing a product by ID (HTML form-based)
@api.route('/html/<int:product_id>/edit')
class ProductEditHTML(Resource):
    def get(self, product_id):
        """Render the edit form for a product."""
        product = Product.query.get_or_404(product_id)
        return render_template('edit_product.html', product=product)

    def post(self, product_id):
        """Handle the form submission to update a product."""
        product = Product.query.get_or_404(product_id)

        try:
            product.name = request.form['name']
            product.description = request.form['description']
            product.price = request.form['price']
            product.quantity_in_stock = request.form['quantity_in_stock']
            product.reorder_point = request.form['reorder_point']
            product.reorder_quantity = request.form['reorder_quantity']

            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            return f"An error occurred: {str(e)}", 500

        return redirect(url_for('main.product_details', product_id=product.id))

# ------------------------------
# API Routes: Handle JSON responses only
# ------------------------------

# Class-based resource for fetching products below the reorder point (API)
@api.route('/api/reorder')
class ProductReorderListAPI(Resource):
    def get(self):
        """Get all products below their reorder point."""
        products_below_reorder = Product.query.filter(Product.quantity_in_stock <= Product.reorder_point).all()

        if not products_below_reorder:
            return jsonify({"message": "No products below reorder point"}), 404

        # Return serializable data
        return jsonify(products_schema.dump(products_below_reorder)), 200


## Class-based resource for fetching products below the reorder point (API)
@api.route('/api/reorder')
class ProductReorderListAPI(Resource):
    def get(self):
        """Get all products below their reorder point."""
        products_below_reorder = Product.query.filter(Product.quantity_in_stock <= Product.reorder_point).all()

        # Check if there are no products below reorder point
        if not products_below_reorder:
            return jsonify({"message": "No products below reorder point"}), 404

        # Correct serialization of product objects
        serialized_data = products_schema.dump(products_below_reorder)

        # Return the properly serialized JSON response
        return jsonify(serialized_data), 200


# Class-based resource for updating a product by ID (API)
@api.route('/api/<int:product_id>')
class ProductUpdateAPI(Resource):
    def put(self, product_id):
        """Update a product by ID (API endpoint for JSON response)."""
        product = Product.query.get_or_404(product_id)
        data = request.json

        errors = product_schema.validate(data, partial=True)
        if errors:
            return jsonify(errors), 400

        if ('name' in data and Product.query.filter(Product.id != product_id, Product.name == data['name']).first()):
            return jsonify({"error": "A product with this name already exists."}), 400

        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.price = data.get('price', product.price)

        db.session.commit()
        return jsonify(product_schema.dump(product)), 200

# Class-based resource for fetching product details by ID (API)
@api.route('/api/<int:product_id>/details')
class ProductDetailsAPI(Resource):
    def get(self, product_id):
        """Get a product by ID (API)."""
        product = Product.query.get_or_404(product_id)
        return product_schema.dump(product), 200
