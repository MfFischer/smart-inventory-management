from datetime import datetime, timedelta
from modules.expenses.models import Expense, Category, OtherIncome
from modules.sales.models import Sale, SaleItem
from modules.products.models import Product
from flask_login import current_user
from modules.inventory.models import Inventory
from modules.accounts_receivable.models import AccountsReceivable
from modules.expenses.models import Expense, OtherIncome
from inventory_system import db
from datetime import datetime
from sqlalchemy import and_
from modules.suppliers.models import AccountsPayable, Supplier
from modules.ReturnedDamagedItem.models import ReturnedDamagedItem
from decimal import Decimal
from flask import current_app
import traceback

def get_time_range(period):
    """
    Returns the start and end dates for a given period (month, quarter, year).
    """
    end_date = datetime.now()
    if period == 'monthly':
        start_date = end_date.replace(day=1)
    elif period == 'quarterly':
        month = (end_date.month - 1) // 3 * 3 + 1
        start_date = end_date.replace(month=month, day=1)
    elif period == 'yearly':
        start_date = end_date.replace(month=1, day=1)
    else:
        start_date = end_date - timedelta(days=30)  # Default to last 30 days if period is undefined
    return start_date, end_date


def fetch_sales_data(user_id, start_date=None, end_date=None):
    """
    Fetch sales data with optional date filtering.
    """
    try:
        # Base query
        query = db.session.query(
            Sale,
            SaleItem,
            Product
        ).select_from(Sale).join(
            SaleItem, Sale.id == SaleItem.sale_id
        ).join(
            Product, SaleItem.product_id == Product.product_id  # Assuming product_id is the correct column name
        )

        # Apply user role-based filtering
        if hasattr(current_user, 'role') and current_user.role == 'admin':
            if hasattr(current_user, 'children'):
                child_ids = [child.id for child in current_user.children]
                query = query.filter(
                    (Sale.user_id == user_id) |
                    (Sale.user_id.in_(child_ids))
                )
            else:
                query = query.filter(Sale.user_id == user_id)
        else:
            query = query.filter(Sale.user_id == user_id)

        # Apply date filters if provided
        if start_date:
            query = query.filter(Sale.created_at >= start_date)
        if end_date:
            query = query.filter(Sale.created_at <= end_date + timedelta(days=1))

        # Execute query and log the SQL for debugging
        sales = query.all()

        # Format the results
        formatted_sales = []
        for sale, sale_item, product in sales:
            formatted_sales.append({
                'sale_date': sale.created_at,
                'customer_name': sale.customer_name,
                'product_name': product.name,
                'quantity': sale_item.quantity,
                'total_price': sale.total_price,
                'sale_status': sale.sale_status
            })

        return formatted_sales

    except Exception as e:
        current_app.logger.error(f"Error fetching sales data: {str(e)}")
        return []

def fetch_expenses_data(user_id, start_date=None, end_date=None):
    """Fetch expenses data and format for visualization."""
    query = Expense.query.filter_by(user_id=user_id)

    if start_date and end_date:
        # Using date_incurred instead of date
        query = query.filter(and_(
            Expense.date_incurred >= start_date,
            Expense.date_incurred <= end_date
        ))

    expenses = query.all()
    return [{
        'date_incurred': expense.date_incurred,
        'amount': float(expense.amount),
        'category': expense.category.name if expense.category else 'Uncategorized',
        'category_name': expense.category.name if expense.category else 'Uncategorized'
    } for expense in expenses]

def fetch_inventory_data(user_id, start_date=None, end_date=None):
    """Fetch inventory data and format for visualization."""
    query = Inventory.query.filter_by(user_id=user_id)

    if start_date and end_date:
        query = query.filter(and_(Inventory.created_at >= start_date, Inventory.created_at <= end_date))

    inventory_items = query.all()
    return [{
        'product_name': item.product.name if item.product else 'Unknown',
        'quantity': item.stock_quantity,
        'value': float(item.stock_quantity * item.cost_price)
    } for item in inventory_items]


def fetch_receivables_data(user_id, start_date=None, end_date=None):
    """Fetch receivables data and format for visualization."""
    query = AccountsReceivable.query.filter_by(user_id=user_id)

    if start_date and end_date:
        query = query.filter(and_(AccountsReceivable.due_date >= start_date,
                                  AccountsReceivable.due_date <= end_date))

    receivables = query.all()
    return [{
        'date': receivable.due_date.strftime('%Y-%m-%d'),
        'amount': float(receivable.amount),
        'status': receivable.status
    } for receivable in receivables]


def fetch_payables_data(user_id, start_date=None, end_date=None):
    """Fetch payables data and format for visualization."""
    query = AccountsPayable.query.filter_by(user_id=user_id)

    if start_date and end_date:
        query = query.filter(and_(AccountsPayable.due_date >= start_date,
                                  AccountsPayable.due_date <= end_date))

    payables = query.all()
    return [{
        'date': payable.due_date.strftime('%Y-%m-%d'),
        'amount': float(payable.amount_due),
        'supplier': payable.supplier.name if payable.supplier else 'Unknown'
    } for payable in payables]

# Update the helper functions to work with the new model structure
def fetch_other_income(user_id, start_date=None, end_date=None):
    """Fetch other income records for a specific user within a date range."""
    try:
        query = OtherIncome.query.filter_by(user_id=user_id)

        if start_date:
            query = query.filter(OtherIncome.date_received >= start_date)
        if end_date:
            query = query.filter(OtherIncome.date_received <= end_date)

        return query.order_by(OtherIncome.date_received.desc()).all()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error fetching other income: {str(e)}")
        return []


def fetch_other_expenses(user_id, start_date=None, end_date=None):
    """Fetch other expenses records for a specific user within a date range."""
    try:
        query = Expense.query.filter_by(user_id=user_id)

        # Add date filters if provided
        if start_date:
            query = query.filter(Expense.date_incurred >= start_date)
        if end_date:
            query = query.filter(Expense.date_incurred <= end_date)

        # Define operating expense categories
        operating_categories = ['salary', 'rent', 'utilities', 'marketing', 'office_supplies']

        # Filter expenses where category name is not in operating categories
        # and expense_type is 'other'
        expenses = query.join(Category).filter(
            Category.name.notin_(operating_categories)
        ).filter(
            Expense.expense_type == 'other'
        ).order_by(Expense.date_incurred.desc()).all()

        return expenses

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error fetching other expenses: {str(e)}")
        return []


def calculate_inventory_turnover(user_id):
    """
    Calculate the inventory turnover rate for a specific user.
    """
    # Sum up the quantity of all sale items for the given user
    total_sales_quantity = (
                               db.session.query(db.func.sum(SaleItem.quantity))
                               .join(Sale, Sale.id == SaleItem.sale_id)
                               .filter(Sale.user_id == user_id)
                               .scalar()
                           ) or 0

    # Sum the inventory stock quantity
    total_inventory = db.session.query(db.func.sum(Inventory.stock_quantity)).filter_by(user_id=user_id).scalar() or 1

    return round(total_sales_quantity / total_inventory, 2)


def calculate_profit_margin(user_id, start_date=None, end_date=None):
    """
    Calculate the profit margin for a specific user within a date range.
    Profit margin = (Total Retail Sales - Total Acquisition Cost) / Total Retail Sales * 100
    """
    try:
        # Fetch sales data within the date range
        sales_data = fetch_sales_data(user_id, start_date, end_date)

        # Calculate total sales from the formatted sales data
        total_sales = Decimal('0')
        if sales_data:
            total_sales = Decimal(str(sum(sale['total_price'] for sale in sales_data)))

        # Get acquisition costs with a separate query
        acquisition_cost_query = db.session.query(
            db.func.sum(Product.cost_price * SaleItem.quantity).label('total_cost')
        ).join(
            SaleItem, Product.product_id == SaleItem.product_id
        ).join(
            Sale, Sale.id == SaleItem.sale_id
        ).filter(Sale.user_id == user_id)

        # Apply date filtering if provided
        if start_date:
            acquisition_cost_query = acquisition_cost_query.filter(Sale.created_at >= start_date)
        if end_date:
            acquisition_cost_query = acquisition_cost_query.filter(Sale.created_at <= end_date + timedelta(days=1))

        # Get the result and ensure it's a Decimal
        acquisition_cost = acquisition_cost_query.scalar() or 0
        acquisition_cost = Decimal(str(acquisition_cost))

        # Calculate profit margin
        if total_sales > 0:
            profit_margin = ((total_sales - acquisition_cost) / total_sales) * Decimal('100')
            return float(round(profit_margin, 2))

        return 0.0

    except Exception as e:
        current_app.logger.error(f"Error calculating profit margin: {str(e)}")
        return 0.0


def calculate_profit_and_loss(user_id, start_date=None, end_date=None):
    """
    Calculate detailed profit and loss statement with categorized entries.
    Returns data structure that exactly matches template requirements.
    """
    try:
        current_app.logger.info(f"Starting profit and loss calculation for user {user_id}")

        # Initialize with a structure that matches template exactly
        data = {
            'revenue': {
                'gross_sales': 0.0,
                'returns': 0.0,
                'net_sales': 0.0
            },
            'cogs': {
                'beginning_inventory': 0.0,
                'purchases': 0.0,
                'ending_inventory': 0.0,
                'total': 0.0
            },
            'operating_expenses': {},
            'gross_profit': 0.0,
            'operating_profit': 0.0,
            'other_items': {
                'total': 0.0
            },
            'net_profit': 0.0
        }

        # Process Sales Data
        sales_data = fetch_sales_data(user_id, start_date, end_date)
        if sales_data:
            # Calculate gross sales (all sales)
            data['revenue']['gross_sales'] = sum(
                float(sale['total_price'])
                for sale in sales_data
                if sale['sale_status'] != 'returned'
            )

            # Calculate returns (returned sales)
            data['revenue']['returns'] = sum(
                float(sale['total_price'])
                for sale in sales_data
                if sale['sale_status'] == 'returned'
            )

            # Calculate net sales
            data['revenue']['net_sales'] = data['revenue']['gross_sales'] - data['revenue']['returns']

        # Process Expenses Data
        expenses_data = fetch_expenses_data(user_id, start_date, end_date)
        expense_categories = {}

        if expenses_data:
            for expense in expenses_data:
                category = expense['category']
                amount = float(expense['amount'])

                if category in expense_categories:
                    expense_categories[category] += amount
                else:
                    expense_categories[category] = amount

        # Add categorized expenses to operating_expenses
        data['operating_expenses'] = expense_categories
        data['operating_expenses']['total'] = sum(expense_categories.values())

        # Calculate profits
        data['gross_profit'] = data['revenue']['net_sales']  # Since we don't have COGS yet
        data['operating_profit'] = data['gross_profit'] - data['operating_expenses']['total']
        data['net_profit'] = data['operating_profit'] + data['other_items']['total']

        current_app.logger.debug(f"Calculated profit and loss data: {data}")
        return data

    except Exception as e:
        current_app.logger.error(f"Error in calculate_profit_and_loss: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return None

def fetch_data_for_report(report_type, user_id, start_date=None, end_date=None):
    if report_type == 'sales':
        return fetch_sales_data(user_id, start_date, end_date)
    elif report_type == 'expenses':
        return fetch_expenses_data(user_id, start_date, end_date)
    elif report_type == 'inventory':
        return fetch_inventory_data(user_id, start_date, end_date)
    elif report_type == 'receivables':
        return fetch_receivables_data(user_id, start_date, end_date)
    elif report_type == 'payables':  # New Accounts Payable report type
        return fetch_payables_data(user_id, start_date, end_date)
    elif report_type == 'profit_loss':
        return calculate_profit_and_loss(user_id, start_date, end_date)
    elif report_type == 'returned_damaged':  # New Returned and Damaged Items report type
        return fetch_returned_damaged_data(user_id, start_date, end_date)
    else:
        raise ValueError("Unknown report type specified.")

def fetch_returned_damaged_data(user_id, start_date=None, end_date=None):
    """
    Fetches data for returned and damaged items for the specified user and date range.
    """
    query = ReturnedDamagedItem.query.filter_by(user_id=user_id)

    # Filter by date range if provided
    if start_date:
        query = query.filter(ReturnedDamagedItem.return_date >= start_date)
    if end_date:
        query = query.filter(ReturnedDamagedItem.return_date <= end_date)

    # Get all returned or damaged items in the specified date range
    returned_items = query.all()

    # Calculate total cost of returned/damaged items
    total_cost = sum(item.quantity * item.inventory.cost_price if item.inventory else 0 for item in returned_items)

    # Calculate the return rate based on total transactions (sales) + returns
    total_transactions = Sale.query.filter_by(user_id=user_id).count()
    total_returns = len(returned_items)
    return_rate = (total_returns / max(total_transactions + total_returns, 1)) * 100  # Avoid division by zero

    # Convert results to a dictionary format for easy rendering
    data = {
        "total_cost": round(total_cost, 2),
        "return_rate": round(return_rate, 2),
        "transactions": [
            {
                "return_date": item.return_date,
                "product_name": item.inventory.product.name if item.inventory else "Unknown",
                "quantity": item.quantity,
                "reason": item.reason,
                "cost_impact": round(item.quantity * item.inventory.cost_price, 2) if item.inventory else 0,
            }
            for item in returned_items
        ],
    }
    return data

def format_data_for_visualization(report_type, data, chart_type='bar', time_period='daily'):
    """
    Formats data for visualization based on report type, chart type, and time period.
    """
    from datetime import datetime
    from collections import defaultdict

    if not data:
        return None

    try:
        formatted_data = []

        if report_type == 'sales':
            # Initialize aggregation dictionaries
            period_totals = defaultdict(float)
            customer_totals = defaultdict(float)

            for sale in data:
                # Handle both dictionary and model object formats
                if isinstance(sale, dict):
                    date = sale.get('sale_date', '') if isinstance(sale.get('sale_date'), datetime) else datetime.strptime(sale.get('sale_date'), '%Y-%m-%d')
                    total_price = float(sale.get('total_price', 0))
                    customer = sale.get('customer_name', 'Unknown')
                else:
                    # Assuming sale is a model object
                    date = sale.sale_date
                    total_price = float(sale.total_price)
                    customer = sale.customer.name if hasattr(sale, 'customer') and sale.customer else 'Unknown'

                # Format period based on time_period selection
                if time_period == 'daily':
                    period_key = date.strftime('%Y-%m-%d')
                elif time_period == 'weekly':
                    period_key = f"Week {date.strftime('%V')} {date.year}"
                elif time_period == 'monthly':
                    period_key = date.strftime('%B %Y')
                else:  # yearly
                    period_key = str(date.year)

                # Aggregate by period
                period_totals[period_key] += total_price
                # Aggregate by customer
                customer_totals[customer] += total_price

            # Format for different chart types
            if chart_type in ['bar', 'line']:
                formatted_data = [
                    {'date': period, 'total_amount': amount}
                    for period, amount in sorted(period_totals.items())
                ]
            elif chart_type == 'pie':
                formatted_data = [
                    {'customer': customer, 'total_amount': amount}
                    for customer, amount in customer_totals.items()
                ]

        elif report_type == 'expenses':
            # Initialize aggregation dictionaries
            period_totals = defaultdict(float)
            category_totals = defaultdict(float)

            for expense in data:
                try:
                    # Handle both dictionary and model object formats
                    if isinstance(expense, dict):
                        date = expense['date_incurred'] if isinstance(expense['date_incurred'], datetime) else datetime.strptime(expense['date_incurred'], '%Y-%m-%d')
                        amount = float(expense['amount'])
                        category = expense['category_name']
                    else:
                        # Assuming expense is a model object
                        date = expense.date_incurred
                        amount = float(expense.amount)
                        category = expense.category.name if expense.category else 'Uncategorized'

                    # Format period based on time_period selection
                    if time_period == 'daily':
                        period_key = date.strftime('%Y-%m-%d')
                    elif time_period == 'weekly':
                        period_key = f"Week {date.strftime('%V')} {date.year}"
                    elif time_period == 'monthly':
                        period_key = date.strftime('%B %Y')
                    else:  # yearly
                        period_key = str(date.year)

                    # Aggregate by period
                    period_totals[period_key] += amount
                    # Aggregate by category
                    category_totals[category] += amount

                except Exception as e:
                    print(f"Error processing expense: {str(e)}")
                    print(f"Expense data: {expense}")
                    continue

            # Format for different chart types
            if chart_type in ['bar', 'line']:
                formatted_data = [
                    {'date': period, 'total_amount': amount}
                    for period, amount in sorted(period_totals.items())
                ]
            elif chart_type == 'pie':
                formatted_data = [
                    {'category': category, 'total_amount': amount}
                    for category, amount in category_totals.items()
                ]

        elif report_type == 'inventory':
            # Process inventory data (inventory doesn't use time periods)
            product_quantities = defaultdict(float)
            product_values = defaultdict(float)

            for item in data:
                # Handle dictionary format
                if isinstance(item, dict):
                    product_name = item.get('product_name', 'Unknown')
                    quantity = float(item.get('quantity', 0))
                    value = float(item.get('value', 0))
                else:
                    # Handle model object format
                    product_name = item.product.name if item.product else 'Unknown'
                    quantity = float(item.stock_quantity)
                    value = float(item.unit_price) * quantity

                # Store both quantity and value
                product_quantities[product_name] = quantity
                product_values[product_name] = value

            # Format based on chart type
            if chart_type in ['bar', 'line']:
                formatted_data = [
                    {'product_name': product, 'total_amount': quantity}
                    for product, quantity in sorted(product_quantities.items())
                ]
            elif chart_type == 'pie':
                formatted_data = [
                    {'product_name': product, 'total_amount': value}
                    for product, value in sorted(product_values.items())
                ]

        print(f"Formatted data for {report_type} ({chart_type}, {time_period}):", formatted_data)
        return formatted_data

    except Exception as e:
        print(f"Error formatting visualization data: {str(e)}")
        print(f"Report type: {report_type}")
        print(f"Chart type: {chart_type}")
        print(f"Time period: {time_period}")
        print(f"Data type: {type(data)}")
        print(f"Data content: {data}")
        return None