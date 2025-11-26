from inventory_system import db
from datetime import datetime

class ReportHistory(db.Model):
    """Store history of generated reports for reference and download."""
    __tablename__ = 'report_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Associate report with a user
    report_type = db.Column(db.String(50), nullable=False)  # e.g., 'sales', 'inventory', 'financial', 'receivables'
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(255), nullable=False)  # Path to stored report file (PDF or Excel)
    status = db.Column(db.String(50), default='completed')  # Status of report generation ('completed', 'failed')
    format = db.Column(db.String(10), nullable=False)  # Format of the report ('pdf' or 'excel')
    generated_by = db.Column(db.String(255), nullable=True)  # Optional: User who generated the report

    # Relationship back to User for easy querying
    user = db.relationship('User', backref='report_history', lazy=True)

    def to_dict(self):
        """Convert the ReportHistory instance to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "report_type": self.report_type,
            "generated_at": self.generated_at,
            "file_path": self.file_path,
            "status": self.status,
            "format": self.format,
            "generated_by": self.generated_by
        }

class ReportSettings(db.Model):
    """Define settings for scheduled and customized reports."""
    __tablename__ = 'report_settings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Associate settings with a user
    report_type = db.Column(db.String(50), nullable=False)  # e.g., 'sales', 'inventory', 'receivables'
    schedule = db.Column(db.String(50), nullable=True)  # e.g., 'daily', 'weekly', 'monthly'
    email_recipients = db.Column(db.Text, nullable=True)  # List of email addresses for scheduled reports
    format = db.Column(db.String(10), default='pdf')  # Default format for the report (PDF or Excel)
    is_enabled = db.Column(db.Boolean, default=True)  # Toggle for enabling/disabling this report

    # Relationship back to User for easy querying
    user = db.relationship('User', backref='report_settings', lazy=True)

    def to_dict(self):
        """Convert the ReportSettings instance to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "report_type": self.report_type,
            "schedule": self.schedule,
            "email_recipients": self.email_recipients.split(",") if self.email_recipients else [],
            "format": self.format,
            "is_enabled": self.is_enabled
        }
