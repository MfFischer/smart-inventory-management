from fpdf import FPDF
from datetime import datetime

def generate_pdf(report_type, data):
    """Generate a PDF file for the specified report."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Header based on report type
    pdf.cell(200, 10, txt=f"{report_type.capitalize()} Report", ln=True, align='C')
    pdf.ln(10)

    if isinstance(data, list):  # Handle data if it's a list
        for item in data:
            pdf.cell(0, 10, txt=str(item), ln=True)  # Convert each item to a string for display
    else:
        pdf.cell(0, 10, txt="No data available.", ln=True)

    pdf_output = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.pdf"
    pdf.output(pdf_output)
    return pdf_output
