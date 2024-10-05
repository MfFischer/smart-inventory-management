from flask import render_template, request, redirect, url_for, jsonify
from inventory_system import db
from modules.sales.models import Sale
from modules.sales.serializers import SaleSchema
from modules.products.models import Product
from marshmallow import ValidationError
from flask_restx import Namespace, Resource

# Define a namespace for sales-related API operations
api = Namespace('sales', description='Sales related operations')

# Initialize the SaleSchema for serialization
sale_schema = SaleSchema()
sales_schema = SaleSchema(many=True)

# Class-based resource for viewing all sales (HTML view)
@api.route('/')
class SaleList(Resource):
    def get(self):
        """Render the sales page with optional search by date."""
        search_date = request.args.get('date')
        if search_date:
            sales = Sale.query.filter(db.func.date(Sale.created_at) == search_date).all()
        else:
            sales = Sale.query.all()
        return render_template('sales.html', sales=sales)

# Class-based resource for getting all sales (API endpoint)
@api.route('/api')
class SalesAPIList(Resource):
    def get(self):
        """Get all sales records (API endpoint)."""
        sales = Sale.query.all()
        return jsonify(sales_schema.dump(sales)), 200

    def post(self):
        """Create a new sale record (API endpoint)."""
        data = request.json
        errors = sale_schema.validate(data)
        if errors:
            return jsonify(errors), 400

        new_sale = Sale(
            product_id=data['product_id'],
            quantity=data['quantity'],
            total_price=data['total_price'],
            sale_status=data.get('sale_status', 'completed')
        )
        db.session.add(new_sale)
        db.session.commit()
        return jsonify(sale_schema.dump(new_sale)), 201

# Class-based resource for handling sale details by ID (HTML view)
@api.route('/<int:sale_id>')
class SaleDetails(Resource):
    def get(self, sale_id):
        """Render the details of a sale by ID (HTML)."""
        sale = Sale.query.get_or_404(sale_id)
        return render_template('sale_details.html', sale=sale)

# Class-based resource for getting a sale by ID (API endpoint)
@api.route('/api/<int:sale_id>')
class SaleDetailAPI(Resource):
    def get(self, sale_id):
        """Get a sale by ID (API endpoint)."""
        sale = Sale.query.get_or_404(sale_id)
        return jsonify(sale_schema.dump(sale)), 200

    def put(self, sale_id):
        """Update a sale record by ID (API endpoint)."""
        sale = Sale.query.get_or_404(sale_id)
        data = request.json
        errors = sale_schema.validate(data, partial=True)
        if errors:
            return jsonify(errors), 400

        sale.product_id = data.get('product_id', sale.product_id)
        sale.quantity = data.get('quantity', sale.quantity)
        sale.total_price = data.get('total_price', sale.total_price)
        sale.sale_status = data.get('sale_status', sale.sale_status)

        db.session.commit()
        return jsonify(sale_schema.dump(sale)), 200

    def delete(self, sale_id):
        """Delete a sale by ID (API endpoint)."""
        sale = Sale.query.get_or_404(sale_id)
        db.session.delete(sale)
        db.session.commit()
        return '', 204

# Class-based resource for adding a sale (HTML form-based)
@api.route('/add')
class SaleCreate(Resource):
    def get(self):
        """Render the form to add a new sale."""
        products = Product.query.all()
        return render_template('add_sale.html', products=products)

    def post(self):
        """Handle form submission to create a new sale."""
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])

        product = Product.query.get(product_id)
        if not product:
            return "Product not found", 404

        total_price = product.price * quantity
        new_sale = Sale(
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
            sale_status=request.form.get('sale_status', 'completed')
        )
        db.session.add(new_sale)
        product.quantity_in_stock -= quantity
        db.session.commit()

        return redirect(url_for('sales.salelist'))

# Class-based resource for editing a sale (HTML form-based)
@api.route('/<int:sale_id>/edit')
class SaleEdit(Resource):
    def get(self, sale_id):
        """Render the form to edit a sale."""
        sale = Sale.query.get_or_404(sale_id)
        return render_template('edit_sale.html', sale=sale)

    def post(self, sale_id):
        """Handle form submission to update a sale."""
        sale = Sale.query.get_or_404(sale_id)
        quantity = int(request.form['quantity'])

        product = Product.query.get(sale.product_id)
        if not product:
            return "Product not found", 404

        total_price = product.price * quantity
        sale.quantity = quantity
        sale.total_price = total_price
        sale.sale_status = request.form['sale_status']

        db.session.commit()

        return redirect(url_for('sales.salelist'))

# Class-based resource for deleting a sale (HTML form-based)
@api.route('/<int:sale_id>/delete')
class SaleDelete(Resource):
    def post(self, sale_id):
        """Delete a sale by ID (HTML form-based)."""
        sale = Sale.query.get_or_404(sale_id)
        db.session.delete(sale)
        db.session.commit()
        return redirect(url_for('sales.salelist'))

# Class-based resource for searching sales by date or other criteria
@api.route('/search')
class SaleSearch(Resource):
    def get(self):
        """Search sales by date or other criteria."""
        query = Sale.query
        date = request.args.get('date')

        if date:
            query = query.filter(Sale.created_at.like(f"%{date}%"))

        sales = query.all()
        return render_template('sales.html', sales=sales)
