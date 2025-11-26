from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app

from modules.users.decorators import role_required
from modules.business.models import Business
from inventory_system import db
import time
import pdfkit
from modules.visualizations.models import Visualization
from modules.tables_reports.report_helpers import (
    fetch_data_for_report,
    format_data_for_visualization,

)
from modules.visualizations.views import create_visualization, get_chart_settings
from modules.visualizations.pdf_helper import generate_pdf
import os
from datetime import datetime

visualizations_bp = Blueprint('visualizations', __name__, template_folder='templates/visualizations')

from datetime import datetime
from flask import (
    current_app, flash, jsonify, redirect, render_template,
    request, url_for
)
from flask_login import current_user, login_required
from functools import wraps


@visualizations_bp.route('/visualize', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_visualization_view():
    """Handle visualization creation and preview."""
    try:
        # Get form data if it's a POST request
        if request.method == 'POST':
            report_type = request.form.get('report_type')
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            chart_type = request.form.get('chart_type')

            print(f"\nVisualization request:")
            print(f"Report type: {report_type}")
            print(f"Date range: {start_date} to {end_date}")
            print(f"Chart type: {chart_type}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return handle_preview_request()
            else:
                return handle_visualization_save()

        # GET request - show the form
        report_types = [
            ('sales', 'Sales Report'),
            ('inventory', 'Inventory Report'),
            ('expenses', 'Expenses Report')
        ]
        chart_types = [
            ('bar', 'Bar Chart'),
            ('line', 'Line Chart'),
            ('pie', 'Pie Chart')
        ]
        return render_template(
            'create_visualization.html',
            report_types=report_types,
            chart_types=chart_types
        )

    except Exception as e:
        current_app.logger.error(f"Error in visualization view: {str(e)}")
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('dashboard'))


def handle_preview_request():
    """Handle AJAX request for chart preview."""
    try:
        # Get form data
        report_type = request.form.get('report_type')
        chart_type = request.form.get('chart_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        print(f"\nHandling preview request:")
        print(f"Report type: {report_type}")
        print(f"Chart type: {chart_type}")
        print(f"Date range: {start_date} to {end_date}")

        # Validate input
        if not all([report_type, chart_type]):
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            })

        # Convert dates if provided
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format'
            })

        # Fetch and format data
        print("Fetching raw data...")
        raw_data = fetch_data_for_report(report_type, current_user.id, start_date, end_date)
        print(f"Raw data received: {raw_data}")

        print("Formatting data...")
        formatted_data = format_data_for_visualization(report_type, raw_data, chart_type)
        print(f"Formatted data: {formatted_data}")

        if not formatted_data:
            return jsonify({
                'success': False,
                'error': 'No data available for the selected parameters'
            })

        # Create visualization
        print("Getting chart settings...")
        chart_settings = get_chart_settings(report_type, chart_type)
        print(f"Chart settings: {chart_settings}")

        print("Creating visualization...")
        chart_html = create_visualization(formatted_data, chart_type, chart_settings)

        if not chart_html:
            return jsonify({
                'success': False,
                'error': 'Failed to generate chart'
            })

        return jsonify({
            'success': True,
            'chart_html': chart_html
        })

    except Exception as e:
        print(f"Error in preview request: {str(e)}")
        current_app.logger.error(f"Error generating preview: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while generating preview'
        })


def handle_visualization_save():
    """Handle saving the visualization with time period aggregation."""
    try:
        # Get form data
        report_type = request.form.get('report_type')
        chart_type = request.form.get('chart_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        time_period = request.form.get('time_period', 'daily')  # New parameter: daily, weekly, monthly, yearly

        print(f"\nHandling visualization save:")
        print(f"Report type: {report_type}")
        print(f"Chart type: {chart_type}")
        print(f"Date range: {start_date} to {end_date}")
        print(f"Time period: {time_period}")

        # Validate input
        if not all([report_type, chart_type, start_date, end_date]):
            flash('Missing required parameters.', 'warning')
            return redirect(url_for('visualizations.create_visualization_view'))

        # Convert dates
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Validate date range based on time period
            date_diff = (end_date - start_date).days

            if time_period == 'daily' and date_diff > 7:
                flash('For daily analysis, please select a range of 7 days or less.', 'warning')
                return redirect(url_for('visualizations.create_visualization_view'))
            elif time_period == 'weekly' and date_diff > 31:
                flash('For weekly analysis, please select a range of 31 days or less.', 'warning')
                return redirect(url_for('visualizations.create_visualization_view'))
            elif time_period == 'monthly' and date_diff > 365:
                flash('For monthly analysis, please select a range of one year or less.', 'warning')
                return redirect(url_for('visualizations.create_visualization_view'))
            elif time_period == 'yearly' and date_diff > 1825:  # 5 years
                flash('For yearly analysis, please select a range of 5 years or less.', 'warning')
                return redirect(url_for('visualizations.create_visualization_view'))

        except ValueError:
            flash('Invalid date format.', 'warning')
            return redirect(url_for('visualizations.create_visualization_view'))

        # Fetch raw data
        print("Fetching raw data...")
        raw_data = fetch_data_for_report(report_type, current_user.id, start_date, end_date)
        print(f"Raw data received: {raw_data}")

        # Format and aggregate data based on time period
        print("Formatting data...")
        formatted_data = format_data_for_visualization(report_type, raw_data, chart_type, time_period)
        print(f"Formatted data: {formatted_data}")

        if not formatted_data:
            flash('No data available for the selected parameters.', 'warning')
            return redirect(url_for('visualizations.create_visualization_view'))

        # Get optimized chart settings
        print("Getting chart settings...")
        chart_settings = get_chart_settings(report_type, chart_type)

        # Update settings based on time period
        title_suffix = f" ({time_period.capitalize()} View)"
        chart_settings.update({
            'layout': {
                'showlegend': True,
                'width': 800,
                'height': 500,
                'margin': {'l': 50, 'r': 50, 't': 50, 'b': 50},
                'font': {'size': 10},
                'paper_bgcolor': 'white',
                'plot_bgcolor': 'white',
                'title': chart_settings.get('title', '') + title_suffix,
                'xaxis': {
                    'tickangle': -45 if time_period in ['monthly', 'yearly'] else 0,
                    'automargin': True
                }
            },
            'config': {
                'responsive': False,
                'displayModeBar': False,
                'displaylogo': False,
                'staticPlot': True,
                'showLink': False
            }
        })

        print("Creating visualization...")
        chart_html = create_visualization(formatted_data, chart_type, chart_settings)

        if not chart_html:
            flash('Failed to generate chart.', 'danger')
            return redirect(url_for('visualizations.create_visualization_view'))

        # Optimize chart HTML
        chart_html = (chart_html
                      .replace('\n', '')
                      .replace('    ', '')
                      .replace('  ', ' ')
                      .replace('> <', '><')
                      )

        # Save visualization
        try:
            visualization = Visualization(
                user_id=current_user.id,
                report_type=report_type,
                chart_type=chart_type,
                start_date=start_date,
                end_date=end_date,
                data=str(formatted_data),
                chart_html=chart_html
            )
            db.session.add(visualization)
            db.session.commit()
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            db.session.rollback()
            flash('Error saving visualization. Please try again.', 'danger')
            return redirect(url_for('visualizations.create_visualization_view'))

        business = Business.query.filter_by(user_id=current_user.id).first()

        return render_template(
            'view_visualization.html',
            chart_html=chart_html,
            vis_id=visualization.id,
            report_type=report_type,
            visualization=visualization,
            business=business
        )

    except Exception as e:
        print(f"Error saving visualization: {str(e)}")
        current_app.logger.error(f"Error saving visualization: {str(e)}")
        flash('Error saving visualization. Please try again.', 'danger')
        return redirect(url_for('visualizations.create_visualization_view'))


def get_chart_settings(report_type, chart_type):
    """Get chart settings based on report and chart type."""
    settings = {
        'sales': {
            'bar': {
                'x': 'date',
                'y': 'total_amount',
                'title': 'Sales Over Time',
                'y_title': 'Amount ($)',
                'x_title': 'Date'
            },
            'line': {
                'x': 'date',
                'y': 'total_amount',
                'title': 'Sales Trends',
                'y_title': 'Amount ($)',
                'x_title': 'Date'
            },
            'pie': {
                'names': 'customer',
                'values': 'total_amount',
                'title': 'Sales by Customer'
            }
        },
        'inventory': {
            'bar': {
                'x': 'product_name',
                'y': 'total_amount',
                'title': 'Current Inventory Levels',
                'y_title': 'Quantity in Stock',
                'x_title': 'Product'
            },
            'line': {
                'x': 'product_name',
                'y': 'total_amount',
                'title': 'Inventory Value Distribution',
                'y_title': 'Value ($)',
                'x_title': 'Product'
            },
            'pie': {
                'names': 'product_name',
                'values': 'total_amount',
                'title': 'Stock Distribution by Product'
            }
        },
        'expenses': {
            'bar': {
                'x': 'date',
                'y': 'total_amount',
                'title': 'Expenses Over Time',
                'y_title': 'Amount ($)',
                'x_title': 'Date'
            },
            'line': {
                'x': 'date',
                'y': 'total_amount',
                'title': 'Expense Trends',
                'y_title': 'Amount ($)',
                'x_title': 'Date'
            },
            'pie': {
                'names': 'category',
                'values': 'total_amount',
                'title': 'Expenses by Category'
            }
        }
    }

    return settings.get(report_type, {}).get(chart_type, {})


@visualizations_bp.route('/preview', methods=['POST'])
@login_required
def preview_visualization():
    try:
        report_type = request.form.get('report_type')
        chart_type = request.form.get('chart_type')
        data = fetch_data_for_report(report_type, current_user.id)

        # Pass chart_type to the formatting function
        formatted_data = format_data_for_visualization(report_type, data, chart_type)

        if formatted_data:
            chart_settings = get_chart_settings(report_type, chart_type)
            chart_html = create_visualization(formatted_data, chart_type, chart_settings)
            return jsonify({'success': True, 'chart_html': chart_html})

        return jsonify({'success': False, 'error': 'No data available'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@visualizations_bp.route('/download/<int:vis_id>')
@login_required
def download_visualization(vis_id):
    """Download visualization as PDF."""
    try:
        # Fetch the visualization from database
        visualization = Visualization.query.get_or_404(vis_id)

        # Check if user has permission to access this visualization
        if visualization.user_id != current_user.id:
            flash("You don't have permission to download this visualization.", "error")
            return redirect(url_for('visualizations.create_visualization_view'))

        # Get business information
        business = Business.query.filter_by(user_id=current_user.id).first()

        # Generate PDF filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"visualization_{visualization.report_type}_{timestamp}.pdf"

        # Create temp directory if it doesn't exist
        temp_dir = os.path.join(current_app.static_folder, 'temp')
        os.makedirs(temp_dir, exist_ok=True)

        output_path = os.path.join(temp_dir, filename)

        # Modify the chart HTML for PDF rendering
        chart_html = visualization.chart_html
        if chart_html:
            # Add custom CSS for PDF rendering
            chart_html = chart_html.replace(
                '</div>',
                '<style>@media print { .js-plotly-plot { height: 500px !important; width: 100% !important; } }</style></div>'
            )

        # Create the PDF content with modified chart
        html_content = render_template(
            'pdf_visualization.html',
            chart_html=chart_html,
            report_type=visualization.report_type,
            created_at=visualization.created_at,
            business=business,
            start_date=visualization.start_date,
            end_date=visualization.end_date
        )

        # Add custom CSS for better PDF rendering
        pdf_options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            'no-outline': None,
            'enable-local-file-access': None
        }

        # Generate PDF with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                pdfkit.from_string(html_content, output_path, options=pdf_options)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(1)  # Wait before retry

        # Send the file
        return send_file(
            output_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        current_app.logger.error(f"Error downloading visualization: {str(e)}")
        flash("Error generating PDF. Please try again.", "error")
        return redirect(url_for('visualizations.create_visualization_view'))

    finally:
        # Clean up temporary file
        try:
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)
        except Exception as e:
            current_app.logger.error(f"Error cleaning up temp file: {str(e)}")