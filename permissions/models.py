from inventory_system import db

# Define the Permission model
class Permission(db.Model):
    """
    Model representing permissions in the system.
    """
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)  # Optional description of the permission

    def __repr__(self):
        return f'<Permission {self.name}>'

# Association table to link users and permissions (Many-to-Many relationship)
user_permissions = db.Table(
    'user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

