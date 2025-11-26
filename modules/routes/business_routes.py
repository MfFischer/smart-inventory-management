from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app
from werkzeug.utils import secure_filename
import os
from flask_login import login_required, current_user
from inventory_system import db
from modules.business.models import Business
from modules.users.models import User

business_bp = Blueprint('business', __name__)


# Create directory for logo uploads
def init_business_directory(app):
    with app.app_context():
        logos_dir = os.path.join(app.static_folder, 'business_logos')
        os.makedirs(logos_dir, exist_ok=True)


@business_bp.record_once
def on_registered(state):
    app = state.app
    init_business_directory(app)


@business_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def business_setup():
    """Handle business setup and updates"""
    # Ensure upload directory exists
    logos_dir = os.path.join(current_app.static_folder, 'business_logos')
    os.makedirs(logos_dir, exist_ok=True)

    # Check if business already exists for user
    existing_business = Business.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        # Get form data
        business_data = {
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'phone': request.form.get('phone'),
            'vat_id': request.form.get('vat_id'),
            'vat_rate': float(request.form.get('vat_rate', 0)),  # Added VAT rate
            'email': request.form.get('email'),
            'website': request.form.get('website')
        }

        # Handle file upload if there's a logo
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename:
                # Generate secure filename and save
                filename = secure_filename(logo.filename)
                filepath = f'business_logos/{current_user.id}_{filename}'
                logo.save(os.path.join(current_app.static_folder, filepath))
                business_data['logo_path'] = filepath

        try:
            if existing_business:
                # Update existing business
                for key, value in business_data.items():
                    if value or value == '' or value == 0:  # Allow empty strings and zero values
                        setattr(existing_business, key, value)
                flash('Business details updated successfully!', 'success')
            else:
                # Create new business
                business_data['user_id'] = current_user.id
                new_business = Business(**business_data)
                db.session.add(new_business)
                flash('Business details saved successfully!', 'success')

            db.session.commit()
            return redirect(url_for('users.personal_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving business details: {str(e)}', 'danger')
            current_app.logger.error(f"Error saving business details: {str(e)}")

    return render_template('business/setup.html', business=existing_business)


@business_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def business_edit():
    """Edit existing business details"""
    business = Business.query.filter_by(user_id=current_user.id).first()
    if not business:
        flash('No business details found. Please set up your business first.', 'warning')
        return redirect(url_for('business.business_setup'))

    if request.method == 'POST':
        try:
            business.name = request.form.get('name')
            business.address = request.form.get('address')
            business.phone = request.form.get('phone')
            business.vat_id = request.form.get('vat_id')
            business.email = request.form.get('email')
            business.website = request.form.get('website')

            # Handle logo upload
            if 'logo' in request.files:
                logo = request.files['logo']
                if logo and logo.filename:
                    # Delete old logo if exists
                    if business.logo_path:
                        try:
                            old_logo_path = os.path.join(current_app.static_folder, business.logo_path)
                            if os.path.exists(old_logo_path):
                                os.remove(old_logo_path)
                        except Exception as e:
                            current_app.logger.error(f"Error removing old logo: {e}")

                    # Save new logo
                    filename = secure_filename(logo.filename)
                    filepath = f'business_logos/{current_user.id}_{filename}'
                    logo.save(os.path.join(current_app.static_folder, filepath))
                    business.logo_path = filepath

            db.session.commit()
            flash('Business details updated successfully!', 'success')
            return redirect(url_for('business.business_view'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating business details: {str(e)}', 'danger')
            current_app.logger.error(f"Error updating business details: {str(e)}")

    return render_template('business/edit.html', business=business)


@business_bp.route('/view')
@login_required
def business_view():
    """View business details"""
    business = Business.query.filter_by(user_id=current_user.id).first()
    if not business:
        flash('No business details found. Please set up your business first.', 'warning')
        return redirect(url_for('business.business_setup'))

    return render_template('business/view.html', business=business)


@business_bp.route('/logo/remove', methods=['POST'])
@login_required
def remove_logo():
    """Remove business logo"""
    business = Business.query.filter_by(user_id=current_user.id).first()
    if business and business.logo_path:
        try:
            # Delete logo file
            logo_path = os.path.join(current_app.static_folder, business.logo_path)
            if os.path.exists(logo_path):
                os.remove(logo_path)

            # Clear logo path in database
            business.logo_path = None
            db.session.commit()
            flash('Logo removed successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error removing logo: {str(e)}', 'danger')
            current_app.logger.error(f"Error removing logo: {str(e)}")

    return redirect(url_for('business.business_edit'))