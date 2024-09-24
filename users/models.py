from inventory_system import db
from passlib.hash import pbkdf2_sha256 as sha256
from datetime import datetime

class Permission(db.Model):
    """
    Permission model representing specific actions or rights that can be assigned to users.
    """
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Permission {self.name}>'


# Association table for the many-to-many relationship between users and permissions
user_permissions = db.Table('user_permissions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'))
)

class User(db.Model):
    """
    User model representing user data in the system.
    """
    __tablename__ = 'users'

    # Primary key for the User table
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Username must be unique and cannot be null
    username = db.Column(db.String(100), unique=True, nullable=False)

    # Hashed password for the user, cannot be null
    hashed_password = db.Column(db.String(255), nullable=False)

    # Optional fields for the user's first and last names
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)

    # Optional email field for the user
    email = db.Column(db.String(255), nullable=True)

    # User role, defaults to 'staff'
    role = db.Column(db.String(50), default='staff')

    # User status, defaults to 'active'
    status = db.Column(db.String(50), default='active')

    # Timestamp for the last login of the user
    last_login = db.Column(db.DateTime, nullable=True)

    # Timestamps for when the user record was created and last updated
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    # Many-to-Many relationship with the Permission model
    permissions = db.relationship(
        'Permission',
        secondary=user_permissions,
        backref=db.backref('users', lazy='dynamic')
    )

    def has_permission(self, permission_name):
        """
        Check if the user has a specific permission.
        """
        return any(permission.name == permission_name for permission in self.permissions)

    def add_permission(self, permission):
        """
        Add a permission to the user.
        """
        if not self.has_permission(permission.name):
            self.permissions.append(permission)
            db.session.commit()

    def remove_permission(self, permission):
        """
        Remove a permission from the user.
        """
        if self.has_permission(permission.name):
            self.permissions.remove(permission)
            db.session.commit()

    def to_dict(self):
        """
        Convert the User object into a dictionary representation.
        """
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "last_login": self.last_login,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "permissions": [permission.name for permission in self.permissions]  # Include permissions in the dictionary
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a User object from a dictionary representation.
        """
        return cls(
            username=data.get('username'),
            hashed_password=cls.generate_hash(data.get('password')),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            role=data.get('role', 'staff'),
            status=data.get('status', 'active')
        )

    @staticmethod
    def generate_hash(password):
        """
        Generate a hash for a given password.
        """
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hashed_password):
        """
        Verify a password against its hash.
        """
        return sha256.verify(password, hashed_password)

    def update_last_login(self):
        """
        Update the last login timestamp.
        """
        self.last_login = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<User {self.username}>'
