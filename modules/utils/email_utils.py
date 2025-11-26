from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os

def send_email_with_sendgrid(to_email, subject, content):
    """
    Send an email using SendGrid.
    """
    message = Mail(
        from_email=os.getenv('MAIL_DEFAULT_SENDER', 'your-email@example.com'),
        to_emails=to_email,
        subject=subject,
        html_content=content)
    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))  # Use API key from environment variables
        response = sg.send(message)
        print(f"Email sent successfully with status code {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
