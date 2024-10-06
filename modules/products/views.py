from flask import request, jsonify, render_template, redirect, url_for
from flask_restx import Namespace, Resource, fields
from modules.products.models import Product
from modules.products.serializers import ProductSchema
from inventory_system import db
from sqlalchemy.exc import SQLAlchemyError

# Define a namespace for the products API (JSON responses only)
api = Namespace('products_api', description='Products API operations')

# Initialize the ProductSchema for validation
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Define the product model for request validation and Swagger documentation
product_model = api.model('Product', {
    'name': fields.String(required=True, description='Product name'),
    'description': fields.String(required=True, description='Product description'),
    'price': fields.Float(required=True, description='Product price'),
    'quantity_in_stock': fields.Integer(required=True, description='Quantity in stock'),
    'reorder_point': fields.Integer(required=True, description='Reorder point')
})

# ------------------------------
# HTML Routes: Move to separate Blueprint or handle directly in main_bp
# ------------------------------

# Class-based resource for rendering all products (HTML view)
@api.route('/html/product_list')
class ProductListHTML(Resource):
    def get(self):
        """Render all products for the HTML view."""
        products = Product.query.all()
        return render_template('products.html',
                               products=products)

# Class-based resource for handling product details (HTML view)
@api.route('/html/<int:product_id>')
class ProductDetailsHTML(Resource):
    def get(self, product_id):
        """Get a product by ID and render the product details page (HTML)."""
        product = Product.query.get_or_404(product_id)
        return render_template('product_details.html',
                               product=product)

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

        return redirect(url_for('products.product_list'))

# Class-based resource for editing a product by ID (HTML form-based)
@api.route('/html/<int:product_id>/edit')
class ProductEditHTML(Resource):
    def get(self, product_id):
        """Render the edit form for a product."""
        product = Product.query.get_or_404(product_id)
        return render_template('edit_product.html',
                               product=product)

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

        return redirect(url_for('main.product_details',
                                product_id=product.id))

# ------------------------------
# API Routes: Handle JSON responses only
# ------------------------------

@api.route('/api/<int:product_id>')
class ProductUpdateAPI(Resource):
    @api.expect(product_model, validate=True)
    def put(self, product_id):
        """Update a product by ID"""
        product = Product.query.get_or_404(product_id)
        data = request.json

        errors = product_schema.validate(data, partial=True)
        if errors:
            return errors, 400

        if 'name' in data and Product.query.filter(
                Product.id != product_id,
                Product.name == data['name']
        ).first():
            return {"error": "A product with this name already exists."}, 400

        for key, value in data.items():
            setattr(product, key, value)

        try:
            db.session.commit()
            return product_schema.dump(product), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500

@api.route('/api/list')
class ProductAPIList(Resource):
    def get(self):
        try:
            products = Product.query.all()
            return products_schema.dump(products), 200
        except SQLAlchemyError as e:
            return {"error": str(e)}, 500

@api.route('/api/create')
class ProductCreateAPI(Resource):
    @api.expect(product_model, validate=True)
    def post(self):
        """Create a new product"""
        data = request.json

        try:
            new_product = Product(**data)
            db.session.add(new_product)
            db.session.commit()
            return product_schema.dump(new_product), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500




