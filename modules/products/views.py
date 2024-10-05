from flask import request, jsonify, render_template, redirect, url_for
from flask_restx import Namespace, Resource
from modules.products.models import Product
from modules.products.serializers import ProductSchema
from inventory_system import db
from modules.suppliers.models import Supplier
from modules.suppliers.serializers import SupplierSchema
from modules.inventory.models import Inventory
from sqlalchemy.exc import SQLAlchemyError

# Define a namespace for the products API
api = Namespace('products', description='Products related operations')

# Initialize the ProductSchema for validation
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Initialize the SupplierSchema for serialization
supplier_schema = SupplierSchema()

# Class-based resource for rendering all products (HTML view)
@api.route('/')
class ProductList(Resource):
    def get(self):
        """Render all products for the HTML view."""
        products = Product.query.all()
        return render_template('products.html', products=products)

# Class-based resource for handling product details (HTML view)
@api.route('/<int:product_id>')
class ProductDetails(Resource):
    def get(self, product_id):
        """Get a product by ID and render the product details page (HTML)."""
        product = Product.query.get_or_404(product_id)
        return render_template('product_details.html', product=product)

# Class-based resource for getting all products (API endpoint for JSON response)
@api.route('/api')
class ProductAPIList(Resource):
    def get(self):
        """Get all products (API endpoint for JSON response)."""
        products = Product.query.all()
        return jsonify(products_schema.dump(products)), 200

# Class-based resource for rendering and handling the create product form
@api.route('/create')
class ProductCreate(Resource):
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

# Class-based resource for editing a product by ID (HTML form-based)
@api.route('/<int:product_id>/edit')
class ProductEdit(Resource):
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

        return redirect(url_for('products.product_details', product_id=product.id))

# Class-based resource for deleting a product by ID
@api.route('/<int:product_id>/delete')
class ProductDelete(Resource):
    def post(self, product_id):
        """Delete a product by ID."""
        product = Product.query.get_or_404(product_id)
        if product.sales:
            return jsonify({"error": "Cannot delete a product with associated sales records."}), 400

        db.session.delete(product)
        db.session.commit()
        return redirect(url_for('products.product_list'))

# Class-based resource for fetching products below the reorder point
@api.route('/api/reorder')
class ProductReorderList(Resource):
    def get(self):
        """Get all products below their reorder point."""
        products_below_reorder = Product.query.filter(Product.quantity_in_stock <= Product.reorder_point).all()
        if not products_below_reorder:
            return jsonify({"message": "No products below reorder point"}), 404
        return products_schema.jsonify(products_below_reorder), 200

# Class-based resource for updating reorder settings of a product
@api.route('/api/<int:product_id>/reorder_settings')
class ProductReorderSettings(Resource):
    def put(self, product_id):
        """Update the reorder point and reorder quantity of a product."""
        product = Product.query.get_or_404(product_id)
        data = request.json

        if 'reorder_point' not in data or 'reorder_quantity' not in data:
            return jsonify({"message": "Reorder point and reorder quantity are required."}), 400

        product.reorder_point = data['reorder_point']
        product.reorder_quantity = data['reorder_quantity']
        db.session.commit()
        return product_schema.jsonify(product), 200

# Class-based resource for searching products
@api.route('/search')
class ProductSearch(Resource):
    def get(self):
        """Search for products."""
        name = request.args.get('name')
        sku = request.args.get('sku')
        supplier_name = request.args.get('supplier')

        query = Product.query
        if name:
            query = query.filter(Product.name.ilike(f'%{name}%'))
        if sku:
            query = query.join(Inventory).filter(Inventory.sku.ilike(f'%{sku}%'))
        if supplier_name:
            query = query.join(Supplier).filter(Supplier.name.ilike(f'%{supplier_name}%'))

        products = query.all()

        if len(products) == 1:
            return redirect(url_for('products.product_details', product_id=products[0].id))

        return render_template('products.html', products=products)

# Class-based resource for fetching product price by ID (API)
@api.route('/api/<int:product_id>/price')
class ProductPrice(Resource):
    def get(self, product_id):
        """Get a product price by ID."""
        product = Product.query.get(product_id)
        if product:
            return jsonify({"price": product.price}), 200
        return jsonify({"error": "Product not found"}), 404

# Class-based resource for fetching product details by ID
@api.route('/<int:product_id>/product-details')
class ProductDetailsForInventory(Resource):
    def get(self, product_id):
        """Get product details by ID (for inventory creation/edit)."""
        product = Product.query.get(product_id)
        if product:
            product_data = {
                'stock_quantity': product.quantity_in_stock,
                'reorder_threshold': product.reorder_point,
                'unit_price': str(product.price)
            }
            return jsonify({'success': True, 'product': product_data}), 200
        return jsonify({'success': False, 'error': 'Product not found'}), 404
