import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Static files configuration
STATIC_FOLDER = os.path.join(BASE_DIR, 'static')
STATIC_URL_PATH = '/static'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Database configuration
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://afe:amara2022@localhost:3306/BMSgo"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret key
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')

# Gmail SMTP Configuration
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = os.getenv('GMAIL_USER')
MAIL_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('GMAIL_USER')

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
STRIPE_MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID')
STRIPE_ANNUAL_PRICE_ID = os.getenv('STRIPE_ANNUAL_PRICE_ID')

# Subscription Prices
MONTHLY_SUBSCRIPTION_PRICE = 14.99
ANNUAL_SUBSCRIPTION_PRICE = 149.90

# Trial Period Settings
TRIAL_PERIOD_DAYS = 14

# Payment Provider Settings
PAYMENT_PROVIDERS = {
    'STRIPE': 'stripe',
}

# Subscription Plan Types
SUBSCRIPTION_PLANS = {
    'MONTHLY': 'monthly',
    'ANNUAL': 'annual'
}

# Subscription Statuses
SUBSCRIPTION_STATUSES = {
    'ACTIVE': 'active',
    'INACTIVE': 'inactive',
    'TRIAL': 'trial',
    'CANCELLED': 'cancelled',
    'EXPIRED': 'expired',
    'PENDING': 'pending'
}

# GDPR Configuration
PRIVACY_POLICY_VERSION = '1.0'
GDPR_DATA_RETENTION_DAYS = 730  # Default 2 years
GDPR_CONTACT_EMAIL = os.getenv('GDPR_CONTACT_EMAIL', 'privacy@example.com')
GDPR_DPO_NAME = os.getenv('GDPR_DPO_NAME', 'Data Protection Officer')
GDPR_DPO_EMAIL = os.getenv('GDPR_DPO_EMAIL', 'dpo@example.com')
