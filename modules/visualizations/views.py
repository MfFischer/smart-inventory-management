import plotly.express as px
import pandas as pd
from datetime import datetime
import pdfkit


def create_visualization(data, chart_type, settings):
    """Generate Plotly chart based on data and settings."""
    try:
        if not data or not settings:
            return None

        print(f"Creating visualization with data: {data}")
        print(f"Chart type: {chart_type}")
        print(f"Settings: {settings}")

        df = pd.DataFrame(data)
        print(f"DataFrame columns: {df.columns}")

        # Get the correct column names based on available data
        x_col = settings.get('x')
        y_col = settings.get('y')

        # Validate that the required columns exist
        if chart_type in ['bar', 'line']:
            if x_col not in df.columns:
                raise ValueError(f"Column '{x_col}' not found in data")
            if y_col not in df.columns:
                raise ValueError(f"Column '{y_col}' not found in data")

        # Common layout settings
        layout_settings = {
            'template': 'plotly_dark',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'font': {'color': 'white', 'size': 12},
            'title': {
                'text': settings.get('title', ''),
                'font': {'size': 24},
                'x': 0.5,
                'xanchor': 'center'
            },
            'height': 600,
            'margin': {'t': 100, 'l': 80, 'r': 80, 'b': 80},
            'showlegend': True
        }

        if chart_type == 'bar':
            fig = px.bar(
                df,
                x=x_col,
                y=y_col,
                title=settings.get('title', ''),
                labels={
                    x_col: settings.get('x_title', ''),
                    y_col: settings.get('y_title', '')
                }
            )

        elif chart_type == 'line':
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=settings.get('title', ''),
                labels={
                    x_col: settings.get('x_title', ''),
                    y_col: settings.get('y_title', '')
                },
                markers=True
            )

        elif chart_type == 'pie':
            names_col = settings.get('names')
            values_col = settings.get('values')

            if names_col not in df.columns or values_col not in df.columns:
                raise ValueError(f"Required columns not found for pie chart")

            fig = px.pie(
                df,
                names=names_col,
                values=values_col,
                title=settings.get('title', '')
            )

        if fig:
            fig.update_layout(**layout_settings)
            return fig.to_html(
                full_html=False,
                include_plotlyjs=True,
                config={
                    'responsive': True,
                    'displayModeBar': True,
                    'displaylogo': False
                }
            )

        return None

    except Exception as e:
        print(f"Error creating visualization: {str(e)}")
        print(f"Data: {data}")
        print(f"Settings: {settings}")
        return None


def get_chart_settings(report_type, chart_type):
    """Get chart settings based on report and chart type."""
    settings = {
        'inventory': {
            'bar': {
                'x': 'product_name',  # Changed from 'date' to 'product_name'
                'y': 'total_amount',
                'title': 'Current Inventory Levels',
                'y_title': 'Quantity in Stock',
                'x_title': 'Product'
            },
            'line': {
                'x': 'product_name',  # Changed from 'date' to 'product_name'
                'y': 'total_amount',
                'title': 'Inventory Value by Product',
                'y_title': 'Value ($)',
                'x_title': 'Product'
            },
            'pie': {
                'names': 'product_name',
                'values': 'total_amount',
                'title': 'Stock Distribution by Product'
            }
        },
        'sales': {
            'bar': {
                'x': 'date',
                'y': 'total_amount',
                'title': 'Sales Analysis',
                'y_title': 'Amount ($)',
                'x_title': 'Date'
            },
            'line': {
                'x': 'date',
                'y': 'total_amount',
                'title': 'Sales Trend',
                'y_title': 'Amount ($)',
                'x_title': 'Date'
            },
            'pie': {
                'names': 'customer',
                'values': 'total_amount',
                'title': 'Sales by Customer'
            }
        },
        'expenses': {
            'bar': {
                'x': 'date',
                'y': 'total_amount',
                'title': 'Expenses Analysis',
                'y_title': 'Amount ($)',
                'x_title': 'Date'
            },
            'line': {
                'x': 'date',
                'y': 'total_amount',
                'title': 'Expenses Trend',
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


def generate_pdf(html_content, output_path):
    """Convert HTML content to a PDF file."""
    try:
        options = {
            'page-size': 'A4',
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'no-outline': None
        }
        pdfkit.from_string(html_content, output_path, options=options)
        return True
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return False