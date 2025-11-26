from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from inventory_system import db
from flask_login import login_required, current_user
from datetime import datetime
from modules.expenses.models import Expense
from modules.users.decorators import role_required
from modules.expenses.models import Expense, Category

expenses_bp = Blueprint('expenses', __name__)

# Comprehensive list of business expense categories with German tax considerations
BUSINESS_EXPENSE_CATEGORIES = {
    "Operating Costs": [
        "Rent and Utilities",
        "Office Supplies",
        "Phone and Internet",
        "Energy Costs",
        "Water and Waste",
        "Cleaning Services"
    ],
    "Employee Related": [
        "Salaries and Wages",
        "Employee Benefits",
        "Training and Education",
        "Work Clothing",
        "Employee Health Insurance",
        "Social Security Contributions"
    ],
    "Professional Services": [
        "Tax Advisor Fees",
        "Legal Fees",
        "Accounting Services",
        "Consulting Fees",
        "IT Services"
    ],
    "Marketing and Sales": [
        "Advertising",
        "Website Costs",
        "Trade Shows",
        "Marketing Materials",
        "Client Gifts (up to €35)",
        "Business Entertainment (70% deductible)"
    ],
    "Travel and Transportation": [
        "Business Travel",
        "Vehicle Expenses",
        "Fuel Costs",
        "Public Transportation",
        "Parking Fees",
        "Vehicle Insurance"
    ],
    "Insurance and Finance": [
        "Business Insurance",
        "Liability Insurance",
        "Professional Insurance",
        "Bank Fees",
        "Interest Payments",
        "Credit Card Fees"
    ],
    "Equipment and Assets": [
        "Office Equipment",
        "Computer Hardware",
        "Software Licenses",
        "Machinery",
        "Furniture",
        "Tools and Equipment"
    ],
    "Maintenance and Repairs": [
        "Building Maintenance",
        "Equipment Repairs",
        "IT Maintenance",
        "Vehicle Maintenance",
        "Property Repairs"
    ],
    "Professional Development": [
        "Training Programs",
        "Conferences",
        "Professional Literature",
        "Subscriptions",
        "Certifications",
        "Professional Memberships"
    ],
    "Research and Development": [
        "Research Materials",
        "Development Costs",
        "Testing Equipment",
        "Prototype Costs",
        "Patent Fees"
    ]
}

# Flatten categories for form display
FLAT_CATEGORIES = [item for sublist in BUSINESS_EXPENSE_CATEGORIES.values() for item in sublist]


@expenses_bp.route('/')
@login_required
@role_required('admin')
def expense_list():
    """Render a list of expenses with filtering and sorting options."""
    try:
        # Get filter parameters
        category = request.args.get('category')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_by = request.args.get('sort_by', 'date_incurred')
        order = request.args.get('order', 'desc')

        # Base query
        query = Expense.query.filter_by(user_id=current_user.id)

        # Apply filters
        if category:
            query = query.filter(Expense.category == category)
        if start_date:
            query = query.filter(Expense.date_incurred >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Expense.date_incurred <= datetime.strptime(end_date, '%Y-%m-%d'))

        # Apply sorting
        if hasattr(Expense, sort_by):
            sort_column = getattr(Expense, sort_by)
            if order == 'desc':
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)

        expenses = query.all()

        return render_template(
            'expense_list.html',  # Changed from 'expenses/expense_list.html'
            expenses=expenses,
            categories=BUSINESS_EXPENSE_CATEGORIES,
            current_filters={
                'category': category,
                'start_date': start_date,
                'end_date': end_date,
                'sort_by': sort_by,
                'order': order
            }
        )

    except Exception as e:
        flash(f"Error loading expenses: {str(e)}", "danger")
        return redirect(url_for('users.personal_dashboard'))


@expenses_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_expense():
    """Handle expense creation with categorized options."""
    try:
        if request.method == 'POST':
            # Get form data
            category_name = request.form.get('new_category') or request.form.get('category')
            description = request.form.get('description')
            amount = request.form.get('amount')
            date_str = request.form.get('date_incurred')

            if not all([category_name, description, amount]):
                flash('Please fill in all required fields.', 'warning')
                return redirect(url_for('expenses.add_expense'))

            try:
                amount = float(amount)
                date_incurred = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
            except ValueError:
                flash('Invalid amount or date format.', 'danger')
                return redirect(url_for('expenses.add_expense'))

            # Get or create category
            category = Category.query.filter_by(
                name=category_name,
                user_id=current_user.id
            ).first()

            if not category:
                # Create new category
                category = Category(
                    name=category_name,
                    user_id=current_user.id,
                    description=f'Category created for {category_name}'
                )
                db.session.add(category)
                try:
                    db.session.flush()  # This will assign an ID to the category
                except Exception as e:
                    db.session.rollback()
                    flash('Error creating new category.', 'danger')
                    print(f"Error creating category: {str(e)}")
                    return redirect(url_for('expenses.add_expense'))

            # Create expense with category relationship
            expense = Expense(
                user_id=current_user.id,
                category_id=category.id,  # Use the category ID
                description=description,
                amount=amount,
                date_incurred=date_incurred
            )

            try:
                db.session.add(expense)
                db.session.commit()
                flash("Expense added successfully!", "success")
                return redirect(url_for('expenses.expense_list'))
            except Exception as e:
                db.session.rollback()
                flash(f"Database error: {str(e)}", "danger")
                return redirect(url_for('expenses.add_expense'))

        # GET request - show form
        # Get all categories for the current user
        categories = Category.query.filter_by(user_id=current_user.id).all()
        category_names = [category.name for category in categories]

        return render_template(
            'add_expense.html',
            categories=BUSINESS_EXPENSE_CATEGORIES,
            existing_categories=category_names
        )

    except Exception as e:
        print(f"Error adding expense: {str(e)}")
        flash(f"Error adding expense: {str(e)}", "danger")
        return redirect(url_for('expenses.add_expense'))


@expenses_bp.route('/<int:expense_id>')
@login_required
@role_required('admin')
def expense_details(expense_id):
    """Show detailed view of an expense with tax deduction information."""
    try:
        expense = Expense.query.get_or_404(expense_id)

        # Ensure user can only view their own expenses
        if expense.user_id != current_user.id:
            flash("You don't have permission to view this expense.", "danger")
            return redirect(url_for('expenses.expense_list'))

        return render_template(
            'expense_details.html',
            expense=expense,
            categories=BUSINESS_EXPENSE_CATEGORIES
        )

    except Exception as e:
        flash(f"Error loading expense details: {str(e)}", "danger")
        return redirect(url_for('expenses.expense_list'))


@expenses_bp.route('/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_expense(expense_id):
    """Handle expense editing with improved error handling and category management."""
    try:
        # Debug log
        current_app.logger.debug(f"Starting edit_expense for ID: {expense_id}")

        # Get the expense or return 404
        expense = Expense.query.get_or_404(expense_id)
        current_app.logger.debug(f"Found expense: {expense.id}")

        # Security check
        if expense.user_id != current_user.id:
            current_app.logger.warning(f"Permission denied for user {current_user.id}")
            flash("You don't have permission to edit this expense.", "danger")
            return redirect(url_for('expenses.expense_list'))

        # Handle POST request
        if request.method == 'POST':
            current_app.logger.debug("Processing POST request")
            try:
                # Get form data
                category_name = request.form.get('new_category') or request.form.get('category')
                description = request.form.get('description')
                amount = request.form.get('amount')
                date_str = request.form.get('date_incurred')

                current_app.logger.debug(
                    f"Form data: category={category_name}, desc={description}, amount={amount}, date={date_str}")

                # Validate required fields
                if not all([category_name, description, amount, date_str]):
                    flash('All fields are required.', 'warning')
                    return redirect(url_for('expenses.edit_expense', expense_id=expense_id))

                # Process category
                category = Category.query.filter_by(
                    name=category_name,
                    user_id=current_user.id
                ).first()

                if not category:
                    current_app.logger.debug(f"Creating new category: {category_name}")
                    category = Category(
                        name=category_name,
                        user_id=current_user.id,
                        description=f'Category created for {category_name}',
                        type='expense'
                    )
                    db.session.add(category)
                    db.session.flush()

                # Update expense
                expense.category_id = category.id
                expense.description = description
                expense.amount = float(amount)
                expense.date_incurred = datetime.strptime(date_str, '%Y-%m-%d')
                expense.updated_at = datetime.now()

                db.session.commit()
                current_app.logger.debug("Successfully updated expense")
                flash("Expense updated successfully!", "success")
                return redirect(url_for('expenses.expense_list'))

            except ValueError as e:
                db.session.rollback()
                current_app.logger.error(f"ValueError: {str(e)}")
                flash("Invalid amount or date format.", "danger")
                return redirect(url_for('expenses.edit_expense', expense_id=expense_id))
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Database error: {str(e)}")
                flash("Error updating expense.", "danger")
                return redirect(url_for('expenses.edit_expense', expense_id=expense_id))

        # Handle GET request
        current_app.logger.debug("Processing GET request")

        # Get all categories including custom ones
        custom_categories = Category.query.filter_by(
            user_id=current_user.id,
            type='expense'
        ).all()
        current_app.logger.debug(f"Found {len(custom_categories)} custom categories")

        # Deep copy the BUSINESS_EXPENSE_CATEGORIES
        categories = BUSINESS_EXPENSE_CATEGORIES.copy()

        # Add custom categories to 'Other' section
        categories['Other'] = [
            cat.name for cat in custom_categories
            if cat.name not in sum(BUSINESS_EXPENSE_CATEGORIES.values(), [])
        ]

        current_app.logger.debug("Preparing to render template")

        # Check if template exists
        import os
        template_path = os.path.join(current_app.root_path, 'templates', 'edit_expense.html')
        current_app.logger.debug(f"Template path: {template_path}")
        current_app.logger.debug(f"Template exists: {os.path.exists(template_path)}")

        # Log the data being passed to template
        current_app.logger.debug(f"Expense data: {expense.to_dict() if hasattr(expense, 'to_dict') else expense}")
        current_app.logger.debug(f"Categories: {categories}")

        try:
            return render_template(
                'edit_expense.html',
                expense=expense,
                categories=categories
            )
        except Exception as template_error:
            current_app.logger.error(f"Template rendering error: {str(template_error)}")
            current_app.logger.exception("Full template error traceback:")
            raise

    except Exception as e:
        current_app.logger.error(f"Error in edit_expense: {str(e)}")
        current_app.logger.exception("Full traceback:")
        flash(f"Error loading expense data: {str(e)}", "danger")
        return redirect(url_for('expenses.expense_list'))