from datetime import datetime
from inventory_system import db
from flask_login import current_user

class Visualization(db.Model):
    __tablename__ = 'visualizations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # E.g., 'sales', 'inventory', etc.
    chart_type = db.Column(db.String(50), nullable=False)   # E.g., 'bar', 'pie', 'line'
    created_at = db.Column(db.DateTime, default=datetime.now)
    start_date = db.Column(db.Date, nullable=True)          # Start of date range for visualization
    end_date = db.Column(db.Date, nullable=True)            # End of date range for visualization
    data = db.Column(db.JSON, nullable=False)               # Store data used in the chart
    chart_url = db.Column(db.String(255), nullable=True)    # URL to generated chart image/file if applicable
    chart_html = db.Column(db.Text(length=4294967295), nullable=True)  # Changed to LONGTEXT

    user = db.relationship('User', backref='visualizations')

    def __repr__(self):
        return f"<Visualization {self.report_type} ({self.chart_type}) by User {self.user_id}>"

    def to_dict(self):
        """Convert visualization to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_type': self.report_type,
            'chart_type': self.chart_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'data': self.data,
            'chart_url': self.chart_url,
            'chart_html': self.chart_html
        }