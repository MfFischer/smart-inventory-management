from flask import Blueprint, render_template, request, redirect, url_for, flash
from inventory_system import db
from modules.accounts_receivable.models import AccountsReceivable
from modules.sales.models import Sale, SaleItem
from modules.products.models import Product
from datetime import datetime, timedelta
from modules.users.decorators import role_required
from flask_login import current_user, login_required

accounts_receivable_bp = Blueprint('accounts_receivable', __name__)


@accounts_receivable_bp.route('/')
@login_required
@role_required('admin', 'staff')
def accounts_receivable_list():
    """Render the list of accounts receivable entries with due date alerts and pending sales for new entries."""
    # Fetch all accounts receivable entries
    receivables = AccountsReceivable.query.all()

    # Get all sales with pending status
    pending_sales = Sale.query.filter_by(sale_status='pending').all()

    # Identify accounts receivable that are due soon or overdue
    due_soon_or_overdue = [
        account for account in receivables
        if account.due_date <= datetime.now() or
           account.due_date <= datetime.now() + timedelta(days=7)
    ]
    due_count = len(due_soon_or_overdue)

    return render_template(
        'accounts_receivable.html',
        receivables=receivables,
        due_count=due_count,
        due_soon_or_overdue=due_soon_or_overdue,
        pending_sales=pending_sales
    )


@accounts_receivable_bp.route('/<int:account_id>')
@login_required
@role_required('admin', 'staff')
def accounts_receivable_details(account_id):
    """Render details of an accounts receivable entry by ID."""
    account = AccountsReceivable.query.get_or_404(account_id)
    sale = Sale.query.get(account.sale_id)
    return render_template('accounts_receivable_details.html', account=account, sale=sale)

@accounts_receivable_bp.route('/<int:account_id>/mark_as_paid', methods=['POST'])
@login_required
@role_required('admin', 'staff')
def accounts_receivable_mark_as_paid(account_id):
    """Mark an accounts receivable entry as paid."""
    account = AccountsReceivable.query.get_or_404(account_id)
    account.status = 'paid'
    db.session.commit()
    flash("Accounts receivable marked as paid.", "success")
    return redirect(url_for('accounts_receivable.accounts_receivable_list'))

@accounts_receivable_bp.route('/<int:account_id>/send_reminder', methods=['POST'])
@login_required
@role_required('admin', 'staff')
def accounts_receivable_send_reminder(account_id):
    """Send a polite reminder email for unpaid accounts receivable."""
    account = AccountsReceivable.query.get_or_404(account_id)
    sale = Sale.query.get(account.sale_id)

    # Generate message details (pseudo-email generation logic)
    reminder_message = f"""
    Dear Customer,

    This is a friendly reminder that you have an outstanding payment for the following items:
    - Sale Date: {sale.sale_date.strftime('%Y-%m-%d')}
    - Total Due: ${account.amount_due}
    - Due Date: {account.due_date.strftime('%Y-%m-%d')}

    Please ensure payment by the due date. Thank you!
    """
    print("Sending reminder email:")
    print(reminder_message)

    flash("Reminder email sent successfully.", "info")
    return redirect(url_for('accounts_receivable.accounts_receivable_details', account_id=account_id))


@accounts_receivable_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def create_accounts_receivable():
    """Create a new accounts receivable entry, optionally from a pending sale."""
    sale_id = request.args.get('sale_id')
    sale = Sale.query.get(sale_id) if sale_id else None

    if sale:
        # Calculate total amount due from sale items
        sale_items = SaleItem.query.filter_by(sale_id=sale.id).all()
        amount_due = sum(item.quantity * item.price_per_unit for item in sale_items)
    else:
        sale_items = []
        amount_due = 0  # Default to 0 if no sale is selected

    if request.method == 'POST':
        customer_name = request.form.get('customer_name')
        amount_due = request.form.get('amount_due')
        due_date = request.form.get('due_date')

        # Create the AccountsReceivable entry with current_user.id
        new_receivable = AccountsReceivable(
            sale_id=sale_id,
            customer_name=customer_name,
            amount_due=amount_due,
            due_date=datetime.strptime(due_date, '%Y-%m-%d'),
            status='pending',
            user_id=current_user.id  # Set user_id to current user
        )

        db.session.add(new_receivable)
        db.session.commit()
        flash("New accounts receivable created successfully.", "success")
        return redirect(url_for('accounts_receivable.accounts_receivable_list'))

    products = Product.query.all()

    return render_template(
        'create_accounts_receivable.html',
        sale=sale,
        sale_items=sale_items,
        products=products,
        amount_due=amount_due
    )

@accounts_receivable_bp.route('/report')
@login_required
@role_required('admin', 'staff')
def accounts_receivable_report():
    """Render the accounts receivable report with total outstanding receivables."""
    # Calculate the total outstanding amount for pending receivables
    total_outstanding = db.session.query(db.func.sum(AccountsReceivable.amount_due)).filter(
        AccountsReceivable.user_id == current_user.id,
        AccountsReceivable.status != 'paid'
    ).scalar() or 0.0

    # Fetch all pending receivables data
    receivables_data = AccountsReceivable.query.filter(
        AccountsReceivable.user_id == current_user.id,
        AccountsReceivable.status != 'paid'
    ).all()

    return render_template(
        'accounts_receivable_report.html',
        receivables_data=receivables_data,
        total_outstanding=total_outstanding
    )
