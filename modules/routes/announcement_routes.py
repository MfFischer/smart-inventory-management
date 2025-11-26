from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from datetime import datetime
import pdfkit
import io
from inventory_system import db
from modules.announcements.models import Announcement
from modules.users.decorators import role_required

# Create the blueprint for announcements
announcements_bp = Blueprint('announcements', __name__, template_folder='templates/announcements')


@announcements_bp.route('/')
@login_required
@role_required('admin', 'staff')
def list_announcements():
    """Display all announcements, sorted by creation date."""
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('list_announcements.html', announcements=announcements)


@announcements_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def create_announcement():
    """Route to create a new announcement."""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        type_ = request.form.get('type')  # e.g., 'announcement', 'event', 'reminder'
        visibility = request.form.get('visibility')  # e.g., 'everyone', 'specific_role'

        announcement = Announcement(
            title=title,
            content=content,
            type=type_,
            visibility=visibility,
            created_by=current_user.id
        )
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement created successfully!', 'success')
        return redirect(url_for('announcements.list_announcements'))

    return render_template('create_announcement.html')


@announcements_bp.route('/<int:announcement_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'staff')
def edit_announcement(announcement_id):
    """Route to edit an existing announcement."""
    announcement = Announcement.query.get_or_404(announcement_id)
    if announcement.created_by != current_user.id:
        flash("You do not have permission to edit this announcement.", "danger")
        return redirect(url_for('announcements.list_announcements'))

    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.content = request.form.get('content')
        announcement.type = request.form.get('type')
        announcement.visibility = request.form.get('visibility')
        announcement.updated_at = datetime.now()
        db.session.commit()
        flash('Announcement updated successfully!', 'success')
        return redirect(url_for('announcements.list_announcements'))

    return render_template('edit_announcement.html', announcement=announcement)


@announcements_bp.route('/<int:announcement_id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'staff')
def delete_announcement(announcement_id):
    try:
        announcement = Announcement.query.get_or_404(announcement_id)

        # Check permissions
        if announcement.created_by != current_user.id:
            flash("You don't have permission to delete this announcement.", "danger")
            return redirect(url_for('announcements.list_announcements'))

        # Store title for flash message
        title = announcement.title

        # Delete the announcement
        db.session.delete(announcement)
        db.session.commit()

        flash(f'Announcement "{title}" has been deleted.', 'success')
        return redirect(url_for('announcements.list_announcements'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting announcement: {str(e)}", "danger")
        return redirect(url_for('announcements.list_announcements'))

@announcements_bp.route('/<int:announcement_id>/download', methods=['GET'])
@login_required
@role_required('admin', 'staff')
def download_announcement(announcement_id):
    """Route to download an announcement as a PDF."""
    try:
        announcement = Announcement.query.get_or_404(announcement_id)
        if announcement.visibility != 'everyone' and announcement.created_by != current_user.id:
            flash("You do not have permission to download this announcement.", "danger")
            return redirect(url_for('announcements.list_announcements'))

        html_content = render_template(
            'announcement_pdf.html',
            announcement=announcement,
            now=datetime.now()
        )

        options = {
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'no-outline': None
        }

        try:
            pdf = pdfkit.from_string(html_content, False, options=options)
        except Exception as e:
            print(f"PDF generation error: {str(e)}")
            flash("Error generating PDF. Please ensure wkhtmltopdf is installed.", "danger")
            return redirect(url_for('announcements.list_announcements'))

        response = send_file(
            io.BytesIO(pdf),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"Announcement_{announcement.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )

        return response

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        flash("Error generating PDF. Please try again.", "danger")
        return redirect(url_for('announcements.list_announcements'))