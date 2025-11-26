from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import current_user, login_required
from modules.sales.models import Sale, SaleItem
from modules.business.models import Business
from sqlalchemy import Case, any_
import traceback
from modules.products.models import Product
from modules.inventory.models import Inventory
from modules.expenses.models import Expense, Category
from modules.accounts_receivable.models import AccountsReceivable
from modules.suppliers.models import AccountsPayable
from modules.tables_reports.models import ReportHistory
from modules.tables_reports.report_helpers import fetch_returned_damaged_data
from modules.tables_reports.pdf_generator import generate_pdf
from modules.users.decorators import role_required
from modules.tables_reports.excel_exporter import export_to_excel
from modules.tables_reports.email_service import send_report_email
from modules.tables_reports.report_helpers import (
    calculate_inventory_turnover, calculate_profit_margin,
     fetch_receivables_data,fetch_expenses_data,
    fetch_data_for_report, calculate_profit_and_loss
)
from datetime import datetime, timedelta
from inventory_system import db
import os

tables_reports_bp = Blueprint('tables_reports', __name__)


@tables_reports_bp.route('/dashboard')
@login_required
@role_required('admin')
def reports_dashboard():
    """Render the reports dashboard with user-specific KPIs."""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

    monthly_revenue = db.session.query(db.func.sum(Sale.total_price)).filter(
        Sale.user_id == current_user.id,
        Sale.sale_date >= datetime.now().replace(day=1)
    ).scalar() or 0

    inventory_turnover = calculate_inventory_turnover(current_user.id)

    # Fetch pending receivables
    pending_receivables = db.session.query(db.func.sum(AccountsReceivable.amount_due)).filter(
        AccountsReceivable.user_id == current_user.id,
        AccountsReceivable.status != 'paid'
    ).scalar() or 0

    # Log the fetched pending receivables
    print("Fetched pending receivables:", pending_receivables)

    # Convert pending receivables to float for display purposes
    pending_receivables = float(pending_receivables) if pending_receivables else 0.0

    profit_margin = calculate_profit_margin(current_user.id, start_date, end_date)

    return render_template('Report_dashboard.html',
                           monthly_revenue=monthly_revenue,
                           inventory_turnover=inventory_turnover,
                           pending_receivables=pending_receivables,
                           profit_margin=profit_margin,
                           start_date=start_date_str,
                           end_date=end_date_str)


@tables_reports_bp.route('/sales_report')
@login_required
def sales_report():
    try:
        # Get date range from request args
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert string dates to datetime objects
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # Include end date

        # Query sales data with proper joins
        query = db.session.query(
            Sale.created_at.label('sale_date'),
            Product.name.label('product_name'),
            SaleItem.quantity,
            SaleItem.price_per_unit.label('unit_price'),  # Changed from unit_price to price_per_unit
            Sale.total_price,
            Sale.sale_status,
            Sale.customer_name
        ).join(
            SaleItem, Sale.id == SaleItem.sale_id
        ).join(
            Product, SaleItem.product_id == Product.product_id
        )

        # Apply date filters if provided
        if start_date and end_date:
            query = query.filter(Sale.created_at.between(start_date, end_date))

        # Apply user filter based on role
        if current_user.role == 'admin':
            # If admin, show all sales for them and their staff
            if hasattr(current_user, 'children'):
                child_ids = [child.id for child in current_user.children]
                query = query.filter(
                    (Sale.user_id == current_user.id) |
                    (Sale.user_id.in_(child_ids))
                )
            else:
                query = query.filter(Sale.user_id == current_user.id)
        else:
            # If not admin, only show their own sales
            query = query.filter(Sale.user_id == current_user.id)

        sales_data = query.order_by(Sale.created_at.desc()).all()

        # Calculate summary statistics
        total_revenue = sum(sale.total_price for sale in sales_data)
        total_sales = len(sales_data)
        total_products = sum(sale.quantity for sale in sales_data)

        # Get business info
        from modules.business.models import Business
        business = Business.query.filter_by(user_id=current_user.id).first()

        return render_template(
            'sales_report.html',
            sales_data=sales_data,
            total_revenue=total_revenue,
            total_sales=total_sales,
            total_products=total_products,
            business=business,
            start_date=start_date,
            end_date=end_date,
            datetime=datetime  # Pass datetime to template
        )

    except Exception as e:
        current_app.logger.error(f"Error generating sales report: {str(e)}")
        flash('Error generating sales report. Please try again.', 'danger')
        return redirect(url_for('tables_reports.reports_dashboard'))


@tables_reports_bp.route('/accounts_receivable_report')
@login_required
def accounts_receivable_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

    # Fetch the receivables data with optional date filtering
    receivables_data = fetch_receivables_data(current_user.id, start_date, end_date)

    # Calculate total outstanding
    total_outstanding = sum(receivable.amount_due for receivable in receivables_data)

    return render_template(
        'accounts_receivable_report.html',
        receivables_data=receivables_data,
        total_outstanding=total_outstanding,
        start_date=start_date_str,
        end_date=end_date_str
    )

@tables_reports_bp.route('/expenses_report')
@login_required
def expenses_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

    expenses_data = fetch_expenses_data(current_user.id, start_date, end_date)
    return render_template('expenses_report.html',
                           expenses_data=expenses_data,
                           start_date=start_date_str,
                           end_date=end_date_str)


@tables_reports_bp.route('/profit_loss_report')
@login_required
def profit_loss_report():
    """Generate a detailed profit and loss statement."""
    try:
        current_app.logger.info("Starting profit and loss report generation")

        # Get date range from request
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        start_date = None
        end_date = None

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD format.', 'danger')
                return redirect(url_for('tables_reports.reports_dashboard'))

        # Calculate profit and loss
        profit_loss_data = calculate_profit_and_loss(current_user.id, start_date, end_date)

        if not profit_loss_data:
            flash('No data available for the selected period.', 'warning')
            return redirect(url_for('tables_reports.reports_dashboard'))

        # Calculate KPIs
        net_sales = profit_loss_data['revenue']['net_sales']
        if net_sales > 0:
            kpis = {
                'gross_margin_percentage': (profit_loss_data['gross_profit'] / net_sales * 100),
                'operating_margin_percentage': (profit_loss_data['operating_profit'] / net_sales * 100),
                'net_profit_margin_percentage': (profit_loss_data['net_profit'] / net_sales * 100)
            }
        else:
            kpis = {
                'gross_margin_percentage': 0.0,
                'operating_margin_percentage': 0.0,
                'net_profit_margin_percentage': 0.0
            }

        # Set period display
        period_length = 'Current Period' if not (start_date and end_date) else None

        # Debug logging
        current_app.logger.debug(f"Profit loss data: {profit_loss_data}")
        current_app.logger.debug(f"KPIs: {kpis}")

        return render_template(
            'profit_loss_report.html',
            profit_loss_data=profit_loss_data,
            kpis=kpis,
            start_date=start_date,
            end_date=end_date,
            period_length=period_length,
            datetime=datetime
        )

    except Exception as e:
        current_app.logger.error(f"Error in profit_loss_report: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash('Error generating profit and loss report. Please try again.', 'danger')
        return redirect(url_for('tables_reports.reports_dashboard'))


@tables_reports_bp.route('/accounts_payable_report')
@login_required
def accounts_payable_report():
    # Get date range from request arguments
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

    # Fetch accounts payable data for the specified user and date range
    payables_data = AccountsPayable.query.filter(
        AccountsPayable.supplier.has(user_id=current_user.id)
    )

    if start_date:
        payables_data = payables_data.filter(AccountsPayable.due_date >= start_date)
    if end_date:
        payables_data = payables_data.filter(AccountsPayable.due_date <= end_date)

    # Retrieve all results and calculate the outstanding total
    payables_data = payables_data.all()
    total_outstanding = sum(item.amount_due for item in payables_data if item.status == 'unpaid')

    # Define and pass accounts_payable_data to the template
    accounts_payable_data = {
        'total_outstanding': total_outstanding,
        'transactions': payables_data
    }

    return render_template(
        'accounts_payable_report.html',
        accounts_payable_data=accounts_payable_data,
        start_date=start_date,
        end_date=end_date
    )

@tables_reports_bp.route('/history')
@login_required
def report_history():
    report_history = ReportHistory.query.filter_by(user_id=current_user.id).order_by(
        ReportHistory.generated_at.desc()).all()
    return render_template('report_history.html',
                           report_history=report_history)



@tables_reports_bp.route('/download/<int:report_id>', methods=['GET'])
@login_required
def download_report(report_id):
    report = ReportHistory.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        flash("You do not have permission to access this report.", "danger")
        return redirect(url_for('tables_reports.report_history'))
    if os.path.exists(report.file_path):
        return send_file(report.file_path, as_attachment=True)
    flash("Report file not found.", "danger")
    return redirect(url_for('tables_reports.report_history'))


@tables_reports_bp.route('/generate/<string:report_type>/<string:format>', methods=['GET', 'POST'])
@login_required
def generate_report(report_type, format):
    # Get start and end dates from the request arguments or form data
    start_date_str = request.args.get('start_date') or request.form.get('start_date')
    end_date_str = request.args.get('end_date') or request.form.get('end_date')

    # Convert date strings to datetime objects if they are provided
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

    try:
        # Fetch data for the report using the provided date range
        data = fetch_data_for_report(report_type, current_user.id, start_date, end_date)
    except Exception as e:
        flash(f"Error fetching data for report: {e}", "danger")
        return redirect(url_for('tables_reports.reports_dashboard'))

    try:
        # Generate the report in the specified format (PDF or Excel)
        if format == 'pdf':
            file_path = generate_pdf(report_type, data)
        elif format == 'excel':
            file_path = export_to_excel(report_type, data)
        else:
            flash("Invalid format specified.", "danger")
            return redirect(url_for('tables_reports.reports_dashboard'))
    except Exception as e:
        flash(f"Error generating {format.upper()} file for {report_type} report: {e}", "danger")
        return redirect(url_for('tables_reports.reports_dashboard'))

    # Save the generated report to the database
    new_report = ReportHistory(
        report_type=report_type,
        file_path=file_path,
        format=format,
        status='completed',
        generated_at=datetime.now(),
        user_id=current_user.id
    )
    db.session.add(new_report)
    db.session.commit()

    flash(f"{report_type.capitalize()} report generated successfully.", "success")
    return redirect(url_for('tables_reports.report_history'))


@tables_reports_bp.route('/send_email/<int:report_id>', methods=['POST'])
@login_required
def send_report_email(report_id):
    report = ReportHistory.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        flash("You do not have permission to send this report.", "danger")
        return redirect(url_for('tables_reports.report_history'))

    recipient_email = request.form.get('email')
    if not recipient_email:
        flash("Please provide an email address.", "danger")
        return redirect(url_for('tables_reports.report_history'))

    success = send_report_email(report.report_type, report.file_path, recipient_email)
    if success:
        flash(f"Report sent to {recipient_email} successfully.", "success")
    else:
        flash("Failed to send the report.", "danger")

    return redirect(url_for('tables_reports.report_history'))


@tables_reports_bp.route('/inventory_report')
@login_required
def inventory_report():
    try:
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert dates if provided
        start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

        # Fetch inventory data using your model's method
        inventory_data = Inventory.get_user_inventory(current_user.id)

        # Apply date filtering if dates are provided
        if start_date or end_date:
            filtered_data = []
            for item in inventory_data:
                if start_date and end_date:
                    if start_date <= item.updated_at <= end_date:
                        filtered_data.append(item)
                elif start_date and item.updated_at >= start_date:
                    filtered_data.append(item)
                elif end_date and item.updated_at <= end_date:
                    filtered_data.append(item)
            inventory_data = filtered_data

        # Calculate totals
        total_items = sum(item.stock_quantity for item in inventory_data)
        total_value = sum(float(item.unit_price) * item.stock_quantity for item in inventory_data)

        # Calculate low stock items count
        low_stock_count = sum(1 for item in inventory_data
                            if item.stock_quantity <= item.reorder_threshold)

        # Get business info
        from modules.business.models import Business
        business = Business.query.filter_by(user_id=current_user.id).first()

        return render_template(
            'inventory_report.html',
            inventory_data=inventory_data,
            total_items=total_items,
            total_value=total_value,
            low_stock_count=low_stock_count,
            period=request.args.get('period', 'monthly'),
            datetime=datetime,
            business=business
        )

    except Exception as e:
        current_app.logger.error(f"Error generating inventory report: {str(e)}")
        flash('Error generating inventory report. Please try again.', 'danger')
        return redirect(url_for('tables_reports.reports_dashboard'))


def fetch_inventory_data(user_id, start_date=None, end_date=None):
    """Fetch inventory data with optional date filtering."""
    try:
        query = db.session.query(
            Inventory
        ).join(
            Product, Inventory.product_id == Product.product_id
        ).filter(
            Product.user_id == user_id
        )

        if start_date:
            query = query.filter(Inventory.last_updated >= start_date)
        if end_date:
            query = query.filter(Inventory.last_updated <= end_date)

        return query.all()

    except Exception as e:
        current_app.logger.error(f"Error fetching inventory data: {str(e)}")
        return []

@tables_reports_bp.route('/returned_damaged_report')
@login_required
def returned_damaged_report():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Convert date strings to datetime objects if provided
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

    # Fetch returned and damaged items data
    returned_damaged_data = fetch_returned_damaged_data(current_user.id, start_date, end_date)

    return render_template(
        'returned_damaged_report.html',
        returned_damaged_data=returned_damaged_data,
        start_date=start_date,
        end_date=end_date
    )
