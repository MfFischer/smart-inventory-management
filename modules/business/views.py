# modules/business/views.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from .models import Business
from inventory_system import db

business_bp = Blueprint('business', __name__)


@business_bp.route('/business/setup', methods=['GET', 'POST'])
@login_required
def business_setup():
    # Check if business already exists for user
    existing_business = Business.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        if existing_business:
            # Update existing business
            existing_business.name = request.form.get('name')
            existing_business.address = request.form.get('address')
            existing_business.phone = request.form.get('phone')
            existing_business.vat_id = request.form.get('vat_id')
            existing_business.email = request.form.get('email')
            existing_business.website = request.form.get('website')

            db.session.commit()
            flash('Business details updated successfully!', 'success')
        else:
            # Create new business
            new_business = Business(
                name=request.form.get('name'),
                address=request.form.get('address'),
                phone=request.form.get('phone'),
                vat_id=request.form.get('vat_id'),
                email=request.form.get('email'),
                website=request.form.get('website'),
                user_id=current_user.id
            )
            db.session.add(new_business)
            db.session.commit()
            flash('Business details saved successfully!', 'success')

        return redirect(url_for('users.personal_dashboard'))

    return render_template('business/setup.html', business=existing_business)
