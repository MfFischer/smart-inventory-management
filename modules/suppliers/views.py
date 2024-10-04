from flask import (Blueprint, render_template,
                   request, redirect, url_for, flash, jsonify)
from inventory_system import db
from modules.suppliers.models import Supplier
from modules.suppliers.serializers import SupplierSchema
from marshmallow import ValidationError

# Blueprint for supplier-related routes
suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/', methods=['GET'])
def get_suppliers():
    """
    Retrieve all suppliers from the database.
    Returns a JSON list of supplier dictionaries.
    """

    # Query all suppliers
    suppliers = Supplier.query.all()
    # Use schema for serializing multiple suppliers
    schema = SupplierSchema(many=True)
    # Return serialized supplier data as JSON
    return jsonify(schema.dump(suppliers)), 200

@suppliers_bp.route('/supplier_details', methods=['GET'])
def supplier_details():
    """
    Render a template showing supplier details.
    Allows searching suppliers by name using the 'search' query parameter.
    """

    # Get search query from request
    search_query = request.args.get('search', '')
    if search_query:
        # Search suppliers whose names contain the search query
        suppliers = Supplier.query.filter(Supplier.name.ilike(f'%{search_query}%')).all()
    else:
        # Fetch all suppliers if no search query is provided
        suppliers = Supplier.query.all()
    return render_template('supplier_details.html', suppliers=suppliers)

@suppliers_bp.route('/create', methods=['GET', 'POST'])
def create_supplier():
    """
    Handle supplier creation.
    Renders the form to create a new supplier and processes the form submission.
    """
    if request.method == 'POST':
        schema = SupplierSchema()  # Schema for validation
        try:
            # Load form data into schema
            supplier_data = schema.load(request.form)
            # Create supplier instance
            supplier = Supplier(**supplier_data)
            # Add supplier to the database
            db.session.add(supplier)
            # Commit the transaction
            db.session.commit()
            # Flash success message
            flash('Supplier created successfully!', 'success')
            # Redirect to details page
            return redirect(url_for('suppliers.supplier_details'))
        except ValidationError as err:
            # Handle validation errors
            flash(f'Error creating supplier: {err.messages}', 'error')
            # Return with error
            return render_template('create_supplier.html'), 400
    # Render the creation form
    return render_template('create_supplier.html')

@suppliers_bp.route('/edit/<int:supplier_id>', methods=['GET', 'POST'])
def edit_supplier(supplier_id):
    """
    Handle editing an existing supplier.
    Renders the edit form and processes form submissions to update the supplier.
    """

    # Fetch supplier by ID or 404
    supplier = Supplier.query.get_or_404(supplier_id)
    if request.method == 'POST':
        # Allow partial updates
        schema = SupplierSchema(partial=True)
        try:
            # Validate form data
            supplier_data = schema.load(request.form)
            for key, value in supplier_data.items():
                # Update supplier fields
                setattr(supplier, key, value)

            # Commit the changes
            db.session.commit()
            # Flash success message
            flash('Supplier updated successfully!', 'success')
            # Redirect to details page
            return redirect(url_for('suppliers.supplier_details'))
        except ValidationError as err:
            # Handle validation errors
            flash(f'Error updating supplier: {err.messages}', 'error')
    # Render the edit form
    return render_template('edit_supplier.html', supplier=supplier)

@suppliers_bp.route('/delete_supplier/<int:supplier_id>', methods=['POST'])
def delete_supplier(supplier_id):
    """
    Handle deleting a supplier by ID.
    Deletes the supplier from the database and redirects to the details page.
    """

    # Fetch supplier by ID or 404
    supplier = Supplier.query.get_or_404(supplier_id)
    # Delete supplier from the database
    db.session.delete(supplier)
    # Commit the transaction
    db.session.commit()
    # Flash success message
    flash('Supplier deleted successfully!', 'success')
    # Redirect to details page
    return redirect(url_for('suppliers.supplier_details'))

@suppliers_bp.route('/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """
    Retrieve a specific supplier by ID.
    Returns a JSON representation of the supplier.
    """

    # Fetch supplier by ID or 404
    supplier = Supplier.query.get_or_404(supplier_id)
    # Schema for serializing supplier data
    schema = SupplierSchema()
    # Return serialized supplier data as JSON
    return jsonify(schema.dump(supplier)), 200

@suppliers_bp.route('/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """
    Handle updating an existing supplier by ID.
    Accepts JSON data and updates the supplier in the database.
    """
    # Fetch supplier by ID or 404
    supplier = Supplier.query.get_or_404(supplier_id)
    # Allow partial updates
    schema = SupplierSchema(partial=True)
    try:
        # Load and validate JSON data
        supplier_data = schema.load(request.json)
        # Update supplier fields
        for key, value in supplier_data.items():
            setattr(supplier, key, value)
        # Commit the changes
        db.session.commit()
        # Return updated supplier as JSON
        return jsonify(schema.dump(supplier)), 200
    except ValidationError as err:
        # Handle validation errors
        return jsonify(err.messages), 400

@suppliers_bp.route('/<int:supplier_id>', methods=['DELETE'])
def api_delete_supplier(supplier_id):
    """
    Handle deleting a supplier by ID (API endpoint).
    Deletes the supplier and returns a 204 (No Content) status.
    """
    # Fetch supplier by ID or 404
    supplier = Supplier.query.get_or_404(supplier_id)
    # Delete supplier from the database
    db.session.delete(supplier)
    # Commit the transaction
    db.session.commit()
    # Return no content
    return '', 204

@suppliers_bp.route('/search', methods=['GET'])
def search_suppliers():
    """
    Handle searching suppliers by name.
    Accepts a query string parameter 'q' and returns matching suppliers as JSON.
    """

    # Get the search query from request
    query = request.args.get('q', '')
    # Search suppliers
    suppliers = Supplier.query.filter(Supplier.name.ilike(f'%{query}%')).all()
    # Use schema for serializing multiple suppliers
    schema = SupplierSchema(many=True)
    # Return serialized supplier data as JSON
    return jsonify(schema.dump(suppliers)), 200
