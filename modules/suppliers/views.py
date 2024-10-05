from flask import render_template, request, redirect, url_for, flash, jsonify
from inventory_system import db
from modules.suppliers.models import Supplier
from modules.suppliers.serializers import SupplierSchema
from marshmallow import ValidationError
from flask_restx import Namespace, Resource

# Define a namespace for supplier-related API operations
api = Namespace('suppliers', description='Suppliers related operations')

# Initialize the SupplierSchema for serialization
supplier_schema = SupplierSchema()
suppliers_schema = SupplierSchema(many=True)

# Class-based resource for getting all suppliers
@api.route('/')
class SupplierList(Resource):
    def get(self):
        """Retrieve all suppliers from the database (JSON)."""
        suppliers = Supplier.query.all()
        return jsonify(suppliers_schema.dump(suppliers)), 200

# Class-based resource for handling supplier details (HTML)
@api.route('/supplier_details')
class SupplierDetails(Resource):
    def get(self):
        """Render a template showing supplier details."""
        search_query = request.args.get('search', '')
        if search_query:
            suppliers = Supplier.query.filter(Supplier.name.ilike(f'%{search_query}%')).all()
        else:
            suppliers = Supplier.query.all()
        return render_template('supplier_details.html', suppliers=suppliers)

# Class-based resource for creating a supplier (HTML + Form)
@api.route('/create')
class SupplierCreate(Resource):
    def get(self):
        """Render the form to create a new supplier."""
        return render_template('create_supplier.html')

    def post(self):
        """Handle supplier creation."""
        schema = SupplierSchema()
        try:
            supplier_data = schema.load(request.form)
            supplier = Supplier(**supplier_data)
            db.session.add(supplier)
            db.session.commit()
            flash('Supplier created successfully!', 'success')
            return redirect(url_for('suppliers.supplierdetails'))
        except ValidationError as err:
            flash(f'Error creating supplier: {err.messages}', 'error')
            return render_template('create_supplier.html'), 400

# Class-based resource for editing a supplier (HTML + Form)
@api.route('/edit/<int:supplier_id>')
class SupplierEdit(Resource):
    def get(self, supplier_id):
        """Render the form for editing an existing supplier."""
        supplier = Supplier.query.get_or_404(supplier_id)
        return render_template('edit_supplier.html', supplier=supplier)

    def post(self, supplier_id):
        """Handle updating an existing supplier."""
        supplier = Supplier.query.get_or_404(supplier_id)
        schema = SupplierSchema(partial=True)
        try:
            supplier_data = schema.load(request.form)
            for key, value in supplier_data.items():
                setattr(supplier, key, value)
            db.session.commit()
            flash('Supplier updated successfully!', 'success')
            return redirect(url_for('suppliers.supplierdetails'))
        except ValidationError as err:
            flash(f'Error updating supplier: {err.messages}', 'error')
        return render_template('edit_supplier.html', supplier=supplier)

# Class-based resource for deleting a supplier
@api.route('/delete_supplier/<int:supplier_id>')
class SupplierDelete(Resource):
    def post(self, supplier_id):
        """Handle deleting a supplier."""
        supplier = Supplier.query.get_or_404(supplier_id)
        db.session.delete(supplier)
        db.session.commit()
        flash('Supplier deleted successfully!', 'success')
        return redirect(url_for('suppliers.supplierdetails'))

# Class-based resource for retrieving a supplier by ID (JSON)
@api.route('/<int:supplier_id>')
class SupplierDetail(Resource):
    def get(self, supplier_id):
        """Retrieve a specific supplier by ID (JSON)."""
        supplier = Supplier.query.get_or_404(supplier_id)
        return jsonify(supplier_schema.dump(supplier)), 200

    def put(self, supplier_id):
        """Update an existing supplier by ID (JSON)."""
        supplier = Supplier.query.get_or_404(supplier_id)
        schema = SupplierSchema(partial=True)
        try:
            supplier_data = schema.load(request.json)
            for key, value in supplier_data.items():
                setattr(supplier, key, value)
            db.session.commit()
            return jsonify(supplier_schema.dump(supplier)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400

    def delete(self, supplier_id):
        """Delete a supplier by ID (JSON)."""
        supplier = Supplier.query.get_or_404(supplier_id)
        db.session.delete(supplier)
        db.session.commit()
        return '', 204

# Class-based resource for searching suppliers (JSON)
@api.route('/search')
class SupplierSearch(Resource):
    def get(self):
        """Handle searching suppliers by name (JSON)."""
        query = request.args.get('q', '')
        suppliers = Supplier.query.filter(Supplier.name.ilike(f'%{query}%')).all()
        return jsonify(suppliers_schema.dump(suppliers)), 200
