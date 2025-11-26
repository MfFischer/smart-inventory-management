from datetime import datetime
from inventory_system import db

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    visibility = db.Column(db.String(50), nullable=False, default="everyone")
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_announcement_creator'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_announcement_owner'), nullable=False)

    # Update relationships
    creator = db.relationship(
        'User',
        backref=db.backref('created_announcements', lazy=True),
        foreign_keys=[created_by]
    )
    owner = db.relationship(
        'User',
        backref=db.backref('owned_announcements', lazy=True),
        foreign_keys=[user_id]
    )

    def __init__(self, title, content, type, visibility, created_by, user_id):
        self.title = title
        self.content = content
        self.type = type
        self.visibility = visibility
        self.created_by = created_by
        self.user_id = user_id