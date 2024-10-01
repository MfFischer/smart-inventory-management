from inventory_system import db

# Association table to link users and permissions (Many-to-Many relationship)
# Ensure this table is defined only once in the application
user_permissions = db.Table(
    'user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True),
    extend_existing=True
)

# Define the Permission model
class Permission(db.Model):
    """
    Model representing permissions in the system.
    """
    __tablename__ = 'permissions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    # Optional description of the permission
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Permission {self.name}>'
