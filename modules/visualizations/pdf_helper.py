import pdfkit
from datetime import datetime


def generate_pdf(html_content, output_path):
    """Convert HTML content to a PDF file with improved formatting."""
    try:
        options = {
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None,
            'footer-right': '[page] of [topage]',
            'footer-font-size': '9',
            'header-font-size': '9',
            'header-left': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'header-right': 'Business Report',
            'header-line': None,
            'footer-line': None
        }

        pdfkit.from_string(
            html_content,
            output_path,
            options=options
        )
        return True
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return False