from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from inventory_system import db
from modules.permissions.models import Permission, user_permissions
from modules.users.decorators import role_required
from flask_login import login_required

permissions_bp = Blueprint('permissions', __name__)

@permissions_bp.route('/manage', methods=['GET'])
@role_required('admin')
@login_required
def manage_permissions():
    """Display all permissions with options to edit or delete."""
    permissions = Permission.query.all()
    return render_template('manage_permissions.html', permissions=permissions)

@permissions_bp.route('/add', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def add_permission():
    """Route to add a new permission."""
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')

        # Check if permission with this name already exists
        if Permission.query.filter_by(name=name).first():
            flash('Permission with this name already exists.', 'error')
            return redirect(url_for('permissions.add_permission'))

        # Create new permission
        new_permission = Permission(name=name, description=description)
        db.session.add(new_permission)
        db.session.commit()

        flash('Permission added successfully!', 'success')
        return redirect(url_for('permissions.manage_permissions'))

    return render_template('add_permission.html')

@permissions_bp.route('/edit/<int:permission_id>', methods=['GET', 'POST'])
@role_required('admin')
@login_required
def edit_permission(permission_id):
    """Route to edit an existing permission."""
    permission = Permission.query.get_or_404(permission_id)

    if request.method == 'POST':
        permission.name = request.form['name']
        permission.description = request.form.get('description', '')

        db.session.commit()
        flash('Permission updated successfully!', 'success')
        return redirect(url_for('permissions.manage_permissions'))

    return render_template('edit_permission.html', permission=permission)

@permissions_bp.route('/delete/<int:permission_id>', methods=['POST'])
@role_required('admin')
@login_required
def delete_permission(permission_id):
    """Route to delete a permission."""
    permission = Permission.query.get_or_404(permission_id)
    db.session.delete(permission)
    db.session.commit()
    flash('Permission deleted successfully!', 'success')
    return redirect(url_for('permissions.manage_permissions'))
