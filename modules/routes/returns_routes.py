from flask import Blueprint, render_template, request, redirect, url_for, flash
from inventory_system import db
from modules.ReturnedDamagedItem.models import ReturnedDamagedItem
from modules.inventory.models import Inventory
from modules.sales.models import Sale
from flask_login import login_required, current_user
from datetime import datetime
from modules.users.decorators import role_required

# Define a blueprint for the returned and damaged items routes
returns_bp = Blueprint('returns', __name__, template_folder='templates/returns')


@returns_bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def list_returns():
    """Display a list of all returned and damaged items with optional search filters."""
    query = ReturnedDamagedItem.query.filter_by(user_id=current_user.id)
    search_date = request.args.get('date')
    search_product = request.args.get('product_name')

    if search_date:
        try:
            date_obj = datetime.strptime(search_date, '%Y-%m-%d')
            query = query.filter(db.func.date(ReturnedDamagedItem.return_date) == date_obj.date())
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")

    if search_product:
        query = query.join(Inventory).filter(Inventory.product_name.ilike(f"%{search_product}%"))

    returned_items = query.all()

    return render_template('list_returns.html', returned_items=returned_items, search_date=search_date,
                           search_product=search_product)


@returns_bp.route('/<int:return_id>')
@login_required
@role_required('admin', 'staff')
def view_return(return_id):
    """Display details of a specific returned or damaged item."""
    returned_item = ReturnedDamagedItem.query.get_or_404(return_id)
    if returned_item.user_id != current_user.id:
        flash("You do not have permission to view this item.", "danger")
        return redirect(url_for('returns.list_returns'))
    return render_template('view_return.html', returned_item=returned_item)


@returns_bp.route('/<int:return_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def edit_return(return_id):
    """Edit a returned or damaged item."""
    returned_item = ReturnedDamagedItem.query.get_or_404(return_id)
    if returned_item.user_id != current_user.id:
        flash("You do not have permission to edit this item.", "danger")
        return redirect(url_for('returns.list_returns'))

    if request.method == 'POST':
        returned_item.quantity = request.form.get('quantity')
        returned_item.reason = request.form.get('reason')
        returned_item.updated_by = current_user.username  # Track who made the edit
        returned_item.updated_at = datetime.now()  # Track when the edit was made
        db.session.commit()
        flash("Returned item updated successfully.", "success")
        return redirect(url_for('returns.list_returns'))

    return render_template('edit_return.html', returned_item=returned_item)


@returns_bp.route('/<int:return_id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'staff')
def delete_return(return_id):
    """Delete a specific returned or damaged item."""
    returned_item = ReturnedDamagedItem.query.get_or_404(return_id)
    if returned_item.user_id != current_user.id:
        flash("You do not have permission to delete this item.", "danger")
        return redirect(url_for('returns.list_returns'))

@returns_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def create_return():
    if request.method == 'POST':
        receipt_number = request.form.get('receipt_number')
        barcode = request.form.get('barcode')
        quantity = int(request.form.get('quantity'))
        reason = request.form.get('reason')

        # Handle return from a sale with receipt number
        sale = None
        if receipt_number:
            sale = Sale.query.filter_by(receipt_number=receipt_number, user_id=current_user.id).first()
            if sale:
                for sale_item in sale.sale_items:
                    if sale_item.product_id:
                        # Update inventory
                        inventory_item = Inventory.query.filter_by(product_id=sale_item.product_id).first()
                        if inventory_item:
                            inventory_item.stock_quantity += quantity
                            db.session.commit()

        # Handle damaged items by barcode
        if barcode:
            inventory_item = Inventory.query.filter(Inventory.sku == barcode).first()
            if inventory_item:
                inventory_item.stock_quantity -= quantity
                db.session.commit()

        new_return = ReturnedDamagedItem(
            inventory_id=inventory_item.id if inventory_item else None,
            sale_id=sale.id if sale else None,
            quantity=quantity,
            reason=reason,
            user_id=current_user.id,
            return_date=datetime.now()
        )
        db.session.add(new_return)
        db.session.commit()

        flash("Return or damaged item record created successfully.", "success")
        return redirect(url_for('returns.list_returns'))

    return render_template('create_return.html')


