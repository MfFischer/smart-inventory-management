from flask import Blueprint, render_template, request, redirect, url_for, flash
from inventory_system import db
from modules.suppliers.models import Supplier
from modules.suppliers.serializers import SupplierSchema
from marshmallow import ValidationError

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/')
def supplier_list():
    """Render a list of suppliers (HTML view)."""
    search_query = request.args.get('search', '')
    if search_query:
        suppliers = Supplier.query.filter(Supplier.name.ilike(f'%{search_query}%')).all()
    else:
        suppliers = Supplier.query.all()
    return render_template('supplier_details.html', suppliers=suppliers)

@suppliers_bp.route('/create', methods=['GET', 'POST'])
def supplier_create():
    """Render the form and handle the creation of a new supplier."""
    if request.method == 'POST':
        schema = SupplierSchema()
        try:
            supplier_data = schema.load(request.form)
            supplier = Supplier(**supplier_data)
            db.session.add(supplier)
            db.session.commit()
            flash('Supplier created successfully!', 'success')
            return redirect(url_for('suppliers.supplier_list'))
        except ValidationError as err:
            flash(f'Error creating supplier: {err.messages}', 'error')
            return render_template('create_supplier.html'), 400

    return render_template('create_supplier.html')

@suppliers_bp.route('/edit/<int:supplier_id>', methods=['GET', 'POST'])
def supplier_edit(supplier_id):
    """Render the form for editing an existing supplier."""
    supplier = Supplier.query.get_or_404(supplier_id)

    if request.method == 'POST':
        schema = SupplierSchema(partial=True)
        try:
            supplier_data = schema.load(request.form)
            for key, value in supplier_data.items():
                setattr(supplier, key, value)
            db.session.commit()
            flash('Supplier updated successfully!', 'success')
            return redirect(url_for('suppliers.supplier_list'))
        except ValidationError as err:
            flash(f'Error updating supplier: {err.messages}', 'error')

    return render_template('edit_supplier.html', supplier=supplier)

@suppliers_bp.route('/delete/<int:supplier_id>', methods=['POST'])
def supplier_delete(supplier_id):
    """Handle the deletion of a supplier."""
    supplier = Supplier.query.get_or_404(supplier_id)
    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted successfully!', 'success')
    return redirect(url_for('suppliers.supplier_list'))

@suppliers_bp.route('/search', methods=['GET'])
def supplier_search():
    """Search suppliers by name (HTML view)."""
    query = request.args.get('search', '')
    suppliers = Supplier.query.filter(Supplier.name.ilike(f'%{query}%')).all()
    return render_template('supplier_details.html', suppliers=suppliers)

