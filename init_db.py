from flask import Flask
from inventory_system import create_app, db
from flask_migrate import Migrate, upgrade

app = create_app()

with app.app_context():
    # Import all models to ensure they're registered with SQLAlchemy
    from modules.users.models import User, SubscriptionPlan, DataAccessRequest
    # Import other models as needed
    
    # Initialize migrations
    migrate = Migrate(app, db)
    
    # Create all tables
    db.create_all()
    
    print("Database tables created successfully!")