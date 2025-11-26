from flask_mail import Message
from modules.tables_reports.pdf_generator import generate_pdf  # Ensure your generator function is imported correctly
from inventory_system import mail

def send_report_email(report_type, data, recipient_email):
    """Send report as an email attachment."""
    msg = Message(
        subject=f"{report_type.capitalize()} Report",
        sender="your_email@example.com",
        recipients=[recipient_email]
    )
    msg.body = f"Please find the attached {report_type} report."

    # Generate report file
    file_path = generate_pdf(report_type, data)  # or export_to_excel if you need Excel format

    with open(file_path, 'rb') as fp:
        msg.attach(file_path, "application/pdf", fp.read())

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
