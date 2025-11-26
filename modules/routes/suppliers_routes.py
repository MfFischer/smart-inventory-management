from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from inventory_system import db
from modules.suppliers.models import Supplier, AccountsPayable
from modules.suppliers.serializers import SupplierSchema
from marshmallow import ValidationError
from datetime import datetime
from modules.suppliers.models import AccountsPayable
from modules.users.decorators import role_required

suppliers_bp = Blueprint('suppliers', __name__)


@suppliers_bp.route('/')
@login_required
@role_required('admin', 'staff')
def supplier_list():
    """Render a list of user-specific suppliers (HTML view)."""
    search_query = request.args.get('search', '')

    if current_user.role == 'admin' or current_user.role == 'owner':
        # Admins and owners see their own suppliers
        user_id = current_user.id
    elif current_user.role == 'staff':
        # Staff users see suppliers belonging to their parent admin/owner
        user_id = current_user.parent_id
    else:
        user_id = None  # Default to None if the role is not recognized

    if user_id:
        if search_query:
            suppliers = Supplier.query.filter(Supplier.user_id == user_id,
                                              Supplier.name.ilike(f'%{search_query}%')).all()
        else:
            suppliers = Supplier.query.filter_by(user_id=user_id).all()
    else:
        suppliers = []  # Default to an empty list if no valid user_id is found

    return render_template('supplier_details.html', suppliers=suppliers)


@suppliers_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def supplier_create():
    """Render the form and handle the creation of a new supplier associated with the current user."""
    if request.method == 'POST':
        schema = SupplierSchema()
        try:
            # Attempt to load data from the form
            supplier_data = schema.load(request.form)
            supplier = Supplier(**supplier_data, user_id=current_user.id)  # Link supplier to the current user
            db.session.add(supplier)
            db.session.commit()
            flash('Supplier created successfully!', 'success')
            return redirect(url_for('suppliers.supplier_list'))
        except ValidationError as err:
            # Log validation error details to console for debugging
            print("Validation Error:", err.messages)  # Debug line
            flash(f'Error creating supplier: {err.messages}', 'error')
            return render_template('create_supplier.html'), 400
        except Exception as e:
            # Log any unexpected errors to help with debugging
            print("Unexpected Error:", str(e))
            flash(f'An unexpected error occurred: {str(e)}', 'error')
            return render_template('create_supplier.html'), 500

    return render_template('create_supplier.html')


@suppliers_bp.route('/edit/<int:supplier_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def supplier_edit(supplier_id):
    """Render the form for editing an existing supplier if the user has access."""
    supplier = Supplier.query.get_or_404(supplier_id)

    # Ensure user can only edit their suppliers
    if supplier.user_id != current_user.id and supplier.user_id != current_user.parent_id:
        flash("You do not have permission to edit this supplier.", "error")
        return redirect(url_for('suppliers.supplier_list'))

    if request.method == 'POST':
        try:
            # Create schema instance with context
            schema = SupplierSchema(context={'supplier_id': supplier_id})

            # Prepare the data
            data = {
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'address': request.form.get('address'),
                'contact': request.form.get('contact'),
                'description': request.form.get('description')
            }

            # Validate and load the data
            validated_data = schema.load(data)

            # Update supplier fields
            for key, value in validated_data.items():
                setattr(supplier, key, value)

            db.session.commit()
            flash('Supplier updated successfully!', 'success')
            return redirect(url_for('suppliers.supplier_list'))

        except ValidationError as err:
            flash(f'Validation error: {err.messages}', 'error')
            return render_template('edit_supplier.html', supplier=supplier)
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating supplier: {str(e)}', 'error')
            return render_template('edit_supplier.html', supplier=supplier)

    return render_template('edit_supplier.html', supplier=supplier)

@suppliers_bp.route('/delete/<int:supplier_id>', methods=['POST'])
@login_required
@role_required('admin', 'staff')
def supplier_delete(supplier_id):
    """Handle the deletion of a supplier if the user has access."""
    supplier = Supplier.query.get_or_404(supplier_id)

    # Ensure user can only delete their suppliers
    if supplier.user_id != current_user.id and supplier.user_id != current_user.parent_id:
        flash("You do not have permission to delete this supplier.", "error")
        return redirect(url_for('suppliers.supplier_list'))

    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted successfully!', 'success')
    return redirect(url_for('suppliers.supplier_list'))

@suppliers_bp.route('/search', methods=['GET'])
@login_required
@role_required('admin', 'staff')
def supplier_search():
    """Search user-specific suppliers by name (HTML view)."""
    query = request.args.get('search', '')
    suppliers = Supplier.get_user_suppliers().filter(Supplier.name.ilike(f'%{query}%')).all()
    return render_template('supplier_details.html', suppliers=suppliers)


@suppliers_bp.route('/<int:supplier_id>/accounts_payable', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def supplier_accounts_payable(supplier_id):
    """View and add accounts payable entries for a supplier."""
    supplier = Supplier.query.get_or_404(supplier_id)

    # Check permissions based on user role
    if current_user.role == 'staff':
        if supplier.user_id != current_user.parent_id:
            flash("You do not have permission to view accounts payable for this supplier.", "error")
            return redirect(url_for('suppliers.supplier_list'))
    else:  # admin
        if supplier.user_id != current_user.id:
            flash("You do not have permission to view accounts payable for this supplier.", "error")
            return redirect(url_for('suppliers.supplier_list'))

    if request.method == 'POST':
        try:
            amount_due = float(request.form.get('amount_due'))
            due_date = request.form.get('due_date')

            # Set user_id based on role
            user_id = current_user.parent_id if current_user.role == 'staff' else current_user.id

            new_payable = AccountsPayable(
                supplier_id=supplier.id,
                user_id=user_id,
                amount_due=amount_due,
                due_date=datetime.strptime(due_date, '%Y-%m-%d'),
                status='unpaid'
            )

            db.session.add(new_payable)
            db.session.commit()
            flash("Accounts payable entry added successfully!", "success")

        except ValueError as e:
            flash(f"Invalid amount or date format: {str(e)}", "error")
            db.session.rollback()
        except Exception as e:
            flash(f"Error adding entry: {str(e)}", "error")
            db.session.rollback()

        return redirect(url_for('suppliers.supplier_accounts_payable', supplier_id=supplier_id))

    # Query accounts payable entries
    if current_user.role == 'staff':
        accounts_payable_entries = AccountsPayable.query.filter_by(
            supplier_id=supplier.id,
            user_id=current_user.parent_id
        ).order_by(AccountsPayable.due_date.desc()).all()
    else:
        accounts_payable_entries = AccountsPayable.query.filter_by(
            supplier_id=supplier.id,
            user_id=current_user.id
        ).order_by(AccountsPayable.due_date.desc()).all()

    return render_template(
        'supplier_accounts_payable.html',
        supplier=supplier,
        accounts_payable_entries=accounts_payable_entries,
        today=datetime.now().strftime('%Y-%m-%d')  # For the date input min attribute
    )


@suppliers_bp.route('/accounts_payable/<int:payable_id>/mark_as_paid', methods=['POST'])
@login_required
@role_required('admin')
def mark_accounts_payable_as_paid(payable_id):
    """Mark an accounts payable entry as paid."""
    payable_entry = AccountsPayable.query.get_or_404(payable_id)

    # Verify user has permission to update this entry
    if payable_entry.user_id != current_user.id and payable_entry.user_id != current_user.parent_id:
        flash("You do not have permission to update this entry.", "error")
        return redirect(url_for('suppliers.supplier_list'))

    try:
        payable_entry.status = 'paid'
        payable_entry.paid_date = datetime.now()
        db.session.commit()
        flash("Accounts payable marked as paid.", "success")
    except Exception as e:
        flash(f"Error updating entry: {str(e)}", "error")
        db.session.rollback()

    return redirect(url_for('suppliers.supplier_accounts_payable', supplier_id=payable_entry.supplier_id))
