from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from inventory_system import db
from modules.announcements.models import Announcement

announcements_bp = Blueprint('announcements', __name__, template_folder='templates/announcements')


@announcements_bp.route('/')
@login_required
def list_announcements():
    """Display a list of all announcements."""
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('list_announcements.html', announcements=announcements)


@announcements_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_announcement():
    """Create a new announcement."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        type_ = request.form.get('type')
        visibility = request.form.get('visibility')

        announcement = Announcement(title=title, content=content, type=type_, visibility=visibility,
                                    created_by=current_user.id)
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement created successfully!', 'success')
        return redirect(url_for('announcements.list_announcements'))

    return render_template('create_announcement.html')


@announcements_bp.route('/<int:announcement_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_announcement(announcement_id):
    """Edit an announcement."""
    announcement = Announcement.query.get_or_404(announcement_id)
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.content = request.form.get('content')
        announcement.type = request.form.get('type')
        announcement.visibility = request.form.get('visibility')
        db.session.commit()
        flash('Announcement updated successfully!', 'success')
        return redirect(url_for('announcements.list_announcements'))

    return render_template('edit_announcement.html', announcement=announcement)


@announcements_bp.route('/<int:announcement_id>/delete', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    """Delete an announcement."""
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    flash('Announcement deleted successfully.', 'success')
    return redirect(url_for('announcements.list_announcements'))
