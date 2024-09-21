from inventory_system import db

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
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a User object from a dictionary representation.
        :param data: Dictionary containing user data.
        :return: User object.
        """
        return cls(
            username=data.get('username'),
            hashed_password=data.get('hashed_password'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            role=data.get('role', 'staff'),
            status=data.get('status', 'active')
        )
