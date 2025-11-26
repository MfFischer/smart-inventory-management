from flask import Blueprint, render_template, request, jsonify
from modules.tables_reports.pdf_generator import generate_pdf
from modules.tables_reports.excel_exporter import export_to_excel
from modules.tables_reports.email_service import send_report_email
from datetime import datetime

tables_reports_bp = Blueprint('tables_reports', __name__)

@tables_reports_bp.route('/dashboard')
def dashboard():
    """Display the main KPIs and summary reports on a dashboard."""
    # Fetch summary data (e.g., sales, inventory levels, financial data)
    # This could be replaced with actual queries to aggregate data from the database.
    summary_data = {
        'monthly_revenue': 45000,
        'inventory_turnover': 1.2,
        'pending_receivables': 8000,
        'profit_margin': 15
    }
    return render_template('Report_dashboard.html', data=summary_data)

@tables_reports_bp.route('/sales_report')
def sales_report():
    """Generate and display a detailed sales report."""
    # Fetch sales data from the database
    # sales_data = Sale.query.all()
    return render_template('sales_report.html', sales_data=sales_data)

@tables_reports_bp.route('/inventory_report')
def inventory_report():
    """Generate and display an inventory report."""
    # Fetch inventory data from the database
    # inventory_data = Inventory.query.all()
    return render_template('inventory_report.html', inventory_data=inventory_data)

@tables_reports_bp.route('/download/<string:report_type>', methods=['POST'])
def download_report(report_type):
    """Download report as PDF or Excel based on report_type."""
    format = request.form.get('format')
    data = {}  # This should contain the data relevant to the report

    if format == 'pdf':
        pdf_file = generate_pdf(report_type, data)
        return pdf_file  # or send as response attachment

    elif format == 'excel':
        excel_file = export_to_excel(report_type, data)
        return excel_file  # or send as response attachment
    return jsonify({"message": "Invalid format"}), 400

@tables_reports_bp.route('/send_report', methods=['POST'])
def send_report():
    """Send report via email."""
    email_address = request.form.get('email')
    report_type = request.form.get('report_type')
    data = {}  # This should contain the data relevant to the report
    success = send_report_email(report_type, data, email_address)
    return jsonify({"message": "Email sent successfully" if success else "Failed to send email"}), 200 if success else 500
