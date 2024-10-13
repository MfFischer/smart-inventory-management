import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database configuration
if os.getenv("FLASK_ENV") == "production":
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
else:
    # Use PostgreSQL locally instead of SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv("DEV_DATABASE_URL", 'sqlite:///' + os.path.join(BASE_DIR, 'app.db'))

SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret key for JWT authentication
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
