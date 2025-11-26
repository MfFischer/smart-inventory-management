from inventory_system import create_app, db
from modules.users.models import User
from datetime import datetime

# Create and set up the Flask app context
app = create_app()
with app.app_context():
    users = User.query.filter(User.trial_expiry_date.isnot(None)).all()
    for user in users:
        if user.is_trial_active() and not user.notification_sent:
            days_remaining = (user.trial_expiry_date - datetime.now()).days
            if days_remaining <= 3:  # Send reminder 3 days before expiry
                user.send_trial_expiry_reminder()
                user.notification_sent = True
                db.session.commit()
