import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database configuration (using SQLite for local development)
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret key for JWT authentication
SECRET_KEY = 'secret_key'


