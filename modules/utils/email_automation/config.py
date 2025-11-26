class EmailConfig:
    """Email configuration settings"""
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 465
    SENDER_NAME = 'BMSgo'
    SUPPORT_EMAIL = 'support@yourdomain.com'
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY = 300  # 5 minutes