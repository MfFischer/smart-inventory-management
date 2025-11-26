from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, g, current_app
from inventory_system import db
from modules.users.models import User, SubscriptionPlan
# Temporarily comment out DataAccessRequest until we can add it to the models
# DataAccessRequest will be added later
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from modules.users.decorators import role_required
from modules.products.models import Product
from modules.inventory.models import Inventory
from modules.accounts_receivable.models import AccountsReceivable
from modules.sales.models import Sale
from modules.suppliers.models import Supplier
from modules.expenses.models import Expense
from datetime import timedelta, datetime, timezone
from modules.ReturnedDamagedItem.models import ReturnedDamagedItem
import stripe
from modules.users.models import User, SubscriptionStatus,  SubscriptionPlan, PaymentProvider
from modules.utils.email_automation import email_automation
from modules.demo.demo_helpers import is_demo_mode, get_demo_stats, get_demo_data


users_bp = Blueprint('users', __name__)

def get_utc_now():
    """Get current UTC time"""
    return datetime.now(timezone.utc)


@users_bp.route('/register', methods=['GET', 'POST'])
def user_register():
    # Get the plan type from query parameters
    selected_plan = request.args.get('plan', 'monthly')

    if request.method == 'POST':
        try:
            current_app.logger.info("Starting registration process")

            # Check existing username
            existing_user = User.query.filter_by(username=request.form['username']).first()
            if existing_user:
                flash('Username already taken. Please choose another.', 'danger')
                return render_template('register.html', selected_plan=selected_plan)

            # Check existing email
            existing_email = User.query.filter_by(email=request.form['email']).first()
            if existing_email:
                flash('Email already registered. Please use another email.', 'danger')
                return render_template('register.html', selected_plan=selected_plan)

            # Create the user
            new_user = User(
                username=request.form['username'],
                email=request.form['email'],
                hashed_password=User.generate_hash(request.form['password'])
            )

            current_app.logger.info(f"Attempting to create user: {new_user.username}")

            db.session.add(new_user)
            db.session.commit()

            current_app.logger.info("User saved to database successfully")

            # Start the trial with selected plan
            new_user.start_trial()

            # Initialize subscription with selected plan
            if new_user.subscription:
                new_user.subscription.plan_type = (
                    SubscriptionPlan.ANNUAL.value if selected_plan == 'annual'
                    else SubscriptionPlan.MONTHLY.value
                )
                db.session.commit()

            current_app.logger.info("Trial started for user")

            # Send welcome email
            try:
                email_automation.send_email(
                    new_user.email,
                    "Welcome to BMSgo!",
                    render_template(
                        'emails/welcome.html',
                        username=new_user.username,
                        trial_days=30,
                        plan_type=selected_plan
                    )
                )
            except Exception as email_error:
                current_app.logger.error(f"Error sending welcome email: {str(email_error)}")

            # Log the user in automatically
            login_user(new_user)

            # Redirect to trial welcome page
            return redirect(url_for('users.trial_welcome'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration failed: {str(e)}")
            flash(f'Registration failed: {str(e)}', 'danger')
            return render_template('register.html', selected_plan=selected_plan)

    # GET request
    return render_template('register.html', selected_plan=selected_plan)


@users_bp.route('/trial-welcome')
@login_required
def trial_welcome():
    """Welcome page after successful trial registration"""
    trial_end_date = current_user.trial_expiry_date
    subscription_info = current_user.get_subscription_details()

    return render_template(
        'trial_welcome.html',
        trial_end_date=trial_end_date,
        subscription_info=subscription_info,
        days_remaining=current_user.get_trial_days_remaining()
    )

@users_bp.before_request
def auto_include_token():
    """Store JWT token from the session into `g` for use in request context."""
    token = session.get('access_token')
    if token and session.get('role') == 'admin':
        g.token = token  # Set token in g for access in request context

@users_bp.route('/users_list')
@login_required
@role_required('admin')
def users_list_view():
    """Render the list of users (Admin only)."""
    # Ensure you fetch all users if no additional filters are needed
    users = User.query.all()
    print(f"Fetched users: {[user.to_dict() for user in users]}")  # Debug print to verify user retrieval
    return render_template('user_list.html', users=users)


@users_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def user_create():
    """Admin-only route for creating a new user."""
    if request.method == 'POST':
        try:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            role = request.form.get('role', 'staff')
            status = request.form.get('status', 'active')
            parent_id = current_user.id if role == 'staff' else None  # Set parent_id for staff

            hashed_password = User.generate_hash(password)
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                role=role,
                status=status,
                parent_id=parent_id  # Assign parent ID
            )

            db.session.add(new_user)
            db.session.commit()

            flash('User created successfully!', 'success')
            return redirect(url_for('users.users_list_view'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Username or Email already exists', 'error')

    parent_users = User.query.filter(User.role == 'admin').all()
    return render_template('create_user.html', parent_users=parent_users)


@users_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def user_edit(user_id):
    """Render the form to edit a user."""
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.role = request.form.get('role')
        user.status = request.form.get('status')
        user.parent_id = request.form.get('parent_id') or None

        try:
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('users.users_list_view'))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Username or Email already exists', 'error')

    parent_users = User.query.filter(User.role == 'admin').all()
    return render_template('edit_user.html', user=user, parent_users=parent_users)

@users_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def user_delete(user_id):
    """Delete a user (Admin only)."""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('users.users_list_view'))


@users_bp.route('/send_trial_reminders', methods=['POST'])
@login_required
@role_required('admin')
def send_trial_reminders():
    """Admin-only route to trigger sending trial expiry reminders."""
    try:
        users = User.query.filter(
            User.trial_expiry_date.isnot(None),
            User.trial_expiry_date > get_utc_now(),
            User.notification_sent.is_(False)
        ).all()

        for user in users:
            if user.is_trial_active():
                days_remaining = user.get_trial_days_remaining()
                if days_remaining <= 7:  # Send reminder for last 7 days
                    email_automation.send_trial_expiry_reminder(user, days_remaining)
                    user.notification_sent = True
                    db.session.commit()

        flash('Trial reminders sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending reminders: {str(e)}', 'danger')

    return redirect(url_for('users.users_list_view'))

@users_bp.route('/personal_dashboard')
@login_required
def personal_dashboard():
    # Check if in demo mode
    if is_demo_mode():
        # Use demo data
        demo_stats = get_demo_stats()
        metrics = {
            'product_count': demo_stats.get('total_products', 0),
            'low_inventory_count': demo_stats.get('low_stock_alerts', 0),
            'supplier_count': 3,  # Demo suppliers
            'inventory_count': demo_stats.get('total_inventory', 0),
            'total_expenses': demo_stats.get('monthly_expenses', 0),
            'accounts_receivable_count': 0,
            'returned_damaged_count': 0,
        }
        subscription_info = {
            'status': 'demo',
            'plan_type': 'Demo Mode',
            'is_active': True
        }
        trial_status = 'demo'
        days_remaining = 0
    else:
        # Determine the correct user for data access
        if current_user.role == 'staff' and current_user.parent:
            admin_user = current_user.parent
        else:
            admin_user = current_user

        # Get subscription and trial information
        subscription_info = admin_user.get_subscription_details()
        trial_status = admin_user.get_trial_status()
        days_remaining = admin_user.get_trial_days_remaining() if admin_user.is_trial_active() else 0

        # Fetch business metrics with UTC time handling
        start_of_month = get_utc_now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        metrics = {
            'product_count': Product.query.filter_by(user_id=admin_user.id).count(),
            'low_inventory_count': Inventory.query.filter(
                Inventory.user_id == admin_user.id,
                Inventory.stock_quantity <= Inventory.reorder_threshold
            ).count(),
            'supplier_count': Supplier.query.filter_by(user_id=admin_user.id).count(),
            'inventory_count': Inventory.query.filter_by(user_id=admin_user.id).count(),
            'total_expenses': Expense.query.filter(
                Expense.user_id == admin_user.id,
                Expense.date_incurred >= start_of_month
            ).with_entities(db.func.sum(Expense.amount)).scalar() or 0,
            'accounts_receivable_count': AccountsReceivable.query.filter(
                AccountsReceivable.user_id == admin_user.id,
                AccountsReceivable.due_date <= (get_utc_now() + timedelta(days=7)),
                AccountsReceivable.status != 'paid'
            ).count(),
            'returned_damaged_count': ReturnedDamagedItem.query.filter_by(user_id=admin_user.id).count(),
        }

    subscription_plans = {
        'monthly': {
            'price': 14.99,
            'features': ['Full access to all features', 'Priority support', 'Unlimited usage']
        },
        'annual': {
            'price': 149.90,
            'savings': 29.98,
            'features': ['All monthly features', '2 months free', 'Priority support', 'Unlimited usage']
        }
    }

    return render_template(
        'personal_dashboard.html',
        metrics=metrics,
        trial_status=trial_status,
        days_remaining=days_remaining,
        subscription_info=subscription_info,
        subscription_plans=subscription_plans
    )

@users_bp.route('/reset_trial', methods=['POST'])
@login_required
def reset_trial():
    """Allow users to reset their trial eligibility after data wipe."""
    if not current_user.is_trial_active():
        try:
            current_user.reset_trial_eligibility()
            flash('Your trial eligibility has been reset. You can register again for a new trial.', 'success')
        except Exception as e:
            flash(f'Error resetting trial: {str(e)}', 'danger')
    else:
        flash('You still have an active trial period.', 'info')
    return redirect(url_for('users.personal_dashboard'))


@users_bp.route('/subscription/start', methods=['POST'])
@login_required
def start_subscription():
    plan_type = request.form.get('plan_type', 'monthly')
    plan_enum = SubscriptionPlan.ANNUAL if plan_type == 'annual' else SubscriptionPlan.MONTHLY

    success, result = current_user.start_paid_subscription(plan_type=plan_enum)

    if success:
        return jsonify({
            'success': True,
            'client_secret': result
        })
    return jsonify({
        'success': False,
        'error': result
    }), 400


@users_bp.route('/subscription/start/<plan>', methods=['GET', 'POST'])
@login_required
def start_subscription_plan(plan):
    """Handle subscription initiation for specific plan"""
    if request.method == 'POST':
        try:
            plan_type = SubscriptionPlan.ANNUAL if plan == 'annual' else SubscriptionPlan.MONTHLY
            success, result = current_user.start_paid_subscription(plan_type=plan_type)

            if success:
                return jsonify({
                    'success': True,
                    'client_secret': result,
                    'public_key': current_app.config.get('STRIPE_PUBLISHABLE_KEY')
                })
            return jsonify({'success': False, 'error': result}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # GET request - show subscription page
    prices = {
        'monthly': {
            'amount': 14.99,
            'interval': 'month',
            'features': ['Full access to all features', 'Priority support', 'Unlimited usage']
        },
        'annual': {
            'amount': 149.90,
            'interval': 'year',
            'savings': 29.98,
            'features': ['All monthly features', '2 months free', 'Priority support', 'Unlimited usage']
        }
    }

    return render_template(
        'subscription.html',
        plan=plan,
        prices=prices,
        stripe_public_key=current_app.config.get('STRIPE_PUBLISHABLE_KEY')
    )


@users_bp.route('/subscription/confirm', methods=['GET'])
@login_required
def confirm_subscription():
    """Handle subscription confirmation after payment"""
    payment_intent_id = request.args.get('payment_intent')

    try:
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if payment_intent.status == 'succeeded':
            if current_user.subscription:
                current_user.subscription.status = SubscriptionStatus.ACTIVE.value
                db.session.commit()

                # Send subscription confirmation email
                email_automation.send_subscription_confirmation(
                    current_user,
                    current_user.subscription.plan_type
                )

                flash('Your subscription has been activated successfully!', 'success')
            else:
                flash('Error: No subscription found.', 'error')
        else:
            flash('Payment was not successful. Please try again.', 'error')
    except Exception as e:
        flash(f'Error confirming subscription: {str(e)}', 'error')

    return redirect(url_for('users.personal_dashboard'))


@users_bp.route('/subscription/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel current subscription"""
    try:
        if current_user.subscription:
            current_user.subscription.status = SubscriptionStatus.CANCELLED.value
            db.session.commit()
            flash('Subscription cancelled successfully.', 'success')
        else:
            flash('No active subscription found.', 'warning')
    except Exception as e:
        flash(f'Error cancelling subscription: {str(e)}', 'error')
    return redirect(url_for('users.personal_dashboard'))


@users_bp.route('/subscription/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            current_app.config.get('STRIPE_WEBHOOK_SECRET')
        )

        # Handle successful payment
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            customer_id = payment_intent.customer
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user and user.subscription:
                user.subscription.status = SubscriptionStatus.ACTIVE.value
                db.session.commit()

                # Send subscription confirmation email
                email_automation.send_subscription_confirmation(
                    user,
                    user.subscription.plan_type
                )

        # Handle failed payment
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            customer_id = payment_intent.customer
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user and user.subscription:
                user.subscription.status = SubscriptionStatus.EXPIRED.value
                db.session.commit()

                # Send payment failed notification
                email_automation.send_payment_failed_notification(
                    user,
                    error_message=payment_intent.get('last_payment_error', {}).get('message')
                )

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@users_bp.route('/trial/<plan_type>')
def trial_redirect(plan_type):
    """Handle redirect for trial signup"""
    if plan_type not in ['monthly', 'annual']:
        flash('Invalid plan type selected.', 'error')
        return redirect(url_for('main.landing'))

    return render_template('trial_redirect.html', plan_type=plan_type)


@users_bp.route('/gdpr/consent', methods=['POST'])
@login_required
def update_gdpr_consent():
    """Update user's GDPR consent preferences"""
    try:
        data = request.json
        user = current_user
        
        # Update consent fields
        user.data_processing_consent = data.get('data_processing_consent', user.data_processing_consent)
        user.marketing_consent = data.get('marketing_consent', user.marketing_consent)
        
        if data.get('data_processing_consent') is True:
            user.consent_date = datetime.now(timezone.utc)
            user.privacy_policy_version = current_app.config.get('PRIVACY_POLICY_VERSION', '1.0')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'GDPR preferences updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating GDPR consent: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# @users_bp.route('/gdpr/request', methods=['POST'])
# @login_required
# def create_data_request():
#     """Create a new GDPR data request (access, deletion, portability)"""
#     try:
#         data = request.json
#         request_type = data.get('request_type')
#         
#         if request_type not in ['access', 'deletion', 'portability']:
#             return jsonify({'success': False, 'message': 'Invalid request type'}), 400
#             
#         # Create new request
#         new_request = DataAccessRequest(
#             user_id=current_user.id,
#             request_type=request_type,
#             request_details=data.get('details', '')
#         )
#         
#         db.session.add(new_request)
#         db.session.commit()
#         
#         return jsonify({'success': True, 'message': 'Request submitted successfully'}), 201
#     except Exception as e:
#         db.session.rollback()
#         return jsonify({'success': False, 'message': str(e)}), 500


