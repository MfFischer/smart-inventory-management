from inventory_system import db
from modules.permissions.models import Permission, user_permissions
from modules.sales.models import Sale
from modules.inventory.models import Inventory
from passlib.hash import pbkdf2_sha256 as sha256
from flask import request, render_template, redirect, url_for, current_app
from flask_login import UserMixin
from modules.utils.email_utils import send_email_with_sendgrid
from datetime import datetime, timedelta
from enum import Enum
import stripe
from datetime import timezone

def get_utc_now():
    """Helper function to get current UTC time"""
    return datetime.now(timezone.utc)

class SubscriptionStatus(Enum):
    TRIAL = 'trial'
    ACTIVE = 'active'
    EXPIRED = 'expired'
    CANCELLED = 'cancelled'

class PaymentProvider(Enum):
    STRIPE = 'stripe'
    PAYPAL = 'paypal'

class SubscriptionPlan(Enum):
    MONTHLY = 'monthly'
    ANNUAL = 'annual'

class Subscription(db.Model):
    """
    Enhanced Subscription model with billing period support
    """
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=SubscriptionStatus.TRIAL.value)
    plan_type = db.Column(db.String(20), nullable=False, default=SubscriptionPlan.MONTHLY.value)
    start_date = db.Column(db.DateTime(timezone=True), default=get_utc_now)
    end_date = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    payment_provider = db.Column(db.String(20), nullable=True)
    payment_provider_subscription_id = db.Column(db.String(255), nullable=True)
    price_id = db.Column(db.String(255), nullable=True)
    amount_paid = db.Column(db.Float, nullable=True)

    def __init__(self, user_id, status=SubscriptionStatus.TRIAL.value,
                 plan_type=SubscriptionPlan.MONTHLY.value):
        self.user_id = user_id
        self.status = status
        self.plan_type = plan_type
        self.start_date = get_utc_now()
        if plan_type == SubscriptionPlan.ANNUAL.value:
            self.end_date = self.start_date + timedelta(days=365)
        else:
            self.end_date = self.start_date + timedelta(days=30)


class User(db.Model, UserMixin):
    """
    User model representing user data in the system.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), default='admin')
    status = db.Column(db.String(50), default='active')
    last_login = db.Column(db.DateTime(timezone=True), nullable=True)
    trial_expiry_date = db.Column(db.DateTime(timezone=True), nullable=True)
    notification_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=get_utc_now,
        onupdate=get_utc_now
    )
    parent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    children = db.relationship("User", backref=db.backref('parent', remote_side=[id]))

    # Subscription related fields
    subscription = db.relationship('Subscription', backref='user', uselist=False)
    stripe_customer_id = db.Column(db.String(255), unique=True, nullable=True)
    paypal_customer_id = db.Column(db.String(255), unique=True, nullable=True)

    permissions = db.relationship(
        Permission,
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

    def assign_all_permissions(self):
        """
        Assign all available permissions to an admin user.
        """
        if self.role == 'admin':
            all_permissions = Permission.query.all()
            current_permissions = {perm.name for perm in self.permissions}
            missing_permissions = [perm for perm in all_permissions if perm.name not in current_permissions]
            if missing_permissions:
                self.permissions.extend(missing_permissions)
                db.session.commit()

    def assign_default_permissions_for_staff(self):
        """
        Assign default permissions for staff members.
        """
        if self.role == 'staff':
            required_permissions = [
                'view_products', 'add_products', 'edit_products',
                'view_sales', 'add_sales', 'edit_sales',
                'view_inventory', 'add_inventory', 'edit_inventory',
                'view_suppliers', 'manage_suppliers',
                'view_announcements', 'add_announcements',
                'view_low_level_alerts', 'add_returned_damaged_items'
            ]
            all_permissions = Permission.query.filter(Permission.name.in_(required_permissions)).all()
            current_permissions = {perm.name for perm in self.permissions}
            missing_permissions = [perm for perm in all_permissions if perm.name not in current_permissions]

            if missing_permissions:
                self.permissions.extend(missing_permissions)
                db.session.commit()

    def get_sales_data(self):
        """
        Retrieve user-specific sales data.
        """
        if self.role == 'owner':
            return Sale.query.filter(Sale.user_id == self.id).all()
        return Sale.query.filter(Sale.user_id == self.parent_id).all()

    def get_inventory_data(self):
        """
        Retrieve user-specific inventory data.
        """
        if self.role == 'owner':
            return Inventory.query.filter(Inventory.user_id == self.id).all()
        return Inventory.query.filter(Inventory.user_id == self.parent_id).all()

    def start_trial(self):
        """
        Set the trial start and expiry date for a new user.
        """
        if not self.trial_expiry_date:
            self.trial_expiry_date = get_utc_now() + timedelta(days=30)
            db.session.commit()  # Commit user first
            self.initialize_subscription()

    def initialize_subscription(self):
        """
        Initialize a new trial subscription
        """
        if not self.subscription:
            try:
                subscription = Subscription(
                    user_id=self.id,
                    status=SubscriptionStatus.TRIAL.value,
                    plan_type=SubscriptionPlan.MONTHLY.value
                )
                db.session.add(subscription)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error initializing subscription: {str(e)}")
                raise

    def start_paid_subscription(self, plan_type=SubscriptionPlan.MONTHLY, payment_provider=PaymentProvider.STRIPE):
        """
        Start a paid subscription
        """
        try:
            if payment_provider == PaymentProvider.STRIPE:
                return self._start_stripe_subscription(plan_type)
            elif payment_provider == PaymentProvider.PAYPAL:
                return self._start_paypal_subscription(plan_type)
        except Exception as e:
            current_app.logger.error(f"Error starting subscription: {str(e)}")
            return False, str(e)

    def _start_stripe_subscription(self, plan_type):
        """
        Initialize a Stripe subscription
        """
        try:
            stripe.api_key = current_app.config['STRIPE_SECRET_KEY']

            # Create or get Stripe customer
            if not self.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=self.email,
                    metadata={'user_id': self.id}
                )
                self.stripe_customer_id = customer.id
                db.session.commit()

            # Select price ID based on plan type
            price_id = (current_app.config['STRIPE_ANNUAL_PRICE_ID']
                       if plan_type == SubscriptionPlan.ANNUAL
                       else current_app.config['STRIPE_MONTHLY_PRICE_ID'])

            # Create subscription
            subscription = stripe.Subscription.create(
                customer=self.stripe_customer_id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent'],
            )

            # Update local subscription record
            if self.subscription:
                self.subscription.status = SubscriptionStatus.ACTIVE.value
                self.subscription.plan_type = plan_type.value
                self.subscription.payment_provider = PaymentProvider.STRIPE.value
                self.subscription.payment_provider_subscription_id = subscription.id
                self.subscription.price_id = price_id
                self.subscription.end_date = (
                    get_utc_now() + timedelta(days=365)
                    if plan_type == SubscriptionPlan.ANNUAL
                    else get_utc_now() + timedelta(days=30)
                )
                db.session.commit()

            return True, subscription.latest_invoice.payment_intent.client_secret

        except stripe.error.StripeError as e:
            return False, str(e)

    def get_subscription_details(self):
        """
        Get subscription details including savings
        """
        if not self.subscription:
            return None

        details = {
            'status': self.subscription.status,
            'plan_type': self.subscription.plan_type,
            'start_date': self.subscription.start_date,
            'end_date': self.subscription.end_date,
            'created_at': self.subscription.created_at,
            'payment_provider': self.subscription.payment_provider
        }

        # Calculate savings for annual plan
        if self.subscription.plan_type == SubscriptionPlan.ANNUAL.value:
            monthly_price = 14.99
            annual_price = 149.90
            details.update({
                'monthly_equivalent': round(annual_price / 12, 2),
                'total_savings': round((monthly_price * 12) - annual_price, 2),
                'free_months': 2
            })

        return details

    def is_trial_active(self):
        """
        Check if trial is active
        """
        if not self.trial_expiry_date:
            return False
        expiry = self.make_aware(self.trial_expiry_date)
        now = get_utc_now()
        return now < expiry

    def make_aware(self, dt):
        """Convert naive datetime to aware datetime"""
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def send_trial_reminder(self):
        """
        Send trial expiry reminder
        """
        if self.trial_expiry_date and not self.notification_sent:
            days_remaining = (self.trial_expiry_date - get_utc_now()).days
            if days_remaining <= 3:
                subject = "Your Trial Is Expiring Soon"
                html = f"""
                <p>Hello {self.username},</p>
                <p>Your 30-day trial will expire in {days_remaining} days. 
                Please subscribe to continue using our Smart Inventory System.</p>
                <p>Choose from our flexible plans:</p>
                <ul>
                    <li>Monthly Plan: $14.99/month</li>
                    <li>Annual Plan: $149.90/year (2 months free!)</li>
                </ul>
                <p>Thank you for using our service!</p>
                """
                send_email_with_sendgrid(self.email, subject, html)
                self.notification_sent = True
                db.session.commit()

    def get_trial_days_remaining(self):
        """
        Get number of days remaining in trial
        """
        if not self.trial_expiry_date:
            return 0
        expiry = self.make_aware(self.trial_expiry_date)
        now = get_utc_now()
        if expiry > now:
            return (expiry - now).days
        return 0

    def get_trial_status(self):
        """
        Get formatted trial status
        """
        if self.is_trial_active():
            days = self.get_trial_days_remaining()
            return f"Active ({days} days remaining)"
        return "Expired"

    def update_last_login(self):
        """
        Update last login timestamp
        """
        self.last_login = get_utc_now()
        db.session.commit()

    def to_dict(self):
        """
        Convert to dictionary
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
            "trial_expiry_date": self.trial_expiry_date,
            "notification_sent": self.notification_sent,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "subscription": self.get_subscription_details(),
            "permissions": [permission.name for permission in self.permissions]
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create from dictionary
        """
        return cls(
            username=data.get('username'),
            hashed_password=cls.generate_hash(data.get('password')),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            role=data.get('role', 'staff'),
            status=data.get('status', 'active'),
            parent_id=data.get('parent_id')
        )

    @staticmethod
    def generate_hash(password):
        """Generate password hash"""
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hashed_password):
        """Verify password hash"""
        return sha256.verify(password, hashed_password)

    def __repr__(self):
        return f'<User {self.username}>'

