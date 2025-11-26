import pandas as pd
from datetime import datetime

def export_to_excel(report_type, data):
    """Generate an Excel file for the specified report with appropriate column names."""
    column_names = {
        'sales': ['Sale ID', 'Product', 'Quantity', 'Total Price', 'Sale Date', 'Customer Name'],
        'inventory': ['Product ID', 'Product Name', 'Stock Quantity', 'Reorder Threshold', 'Unit Price', 'Last Updated'],
        'receivables': ['Receivable ID', 'Customer Name', 'Amount Due', 'Due Date', 'Status'],
        'profit_loss': ['Profit', 'Loss', 'Net Income'],  # Example summary structure
        'expenses': ['Expense ID', 'Category', 'Amount', 'Date Incurred', 'Description'],
        'payables': ['Payable ID', 'Supplier Name', 'Amount Due', 'Due Date', 'Status'],
        'returned_damaged': ['Item ID', 'Product Name', 'Reason', 'Date Returned', 'Condition'],
    }

    # Map column names if provided in the structure
    if isinstance(data, list) and data and isinstance(data[0], dict):
        # If data is a list of dictionaries, convert it to a DataFrame
        df = pd.DataFrame(data)
        # Rename columns based on the report type if applicable
        if report_type in column_names:
            df.columns = column_names.get(report_type, df.columns)
    elif isinstance(data, dict):
        # If data is a single summary dictionary, convert it to a DataFrame with a single row
        df = pd.DataFrame([data])
        if report_type in column_names:
            df.columns = column_names.get(report_type, df.columns)
    else:
        raise ValueError(f"Invalid data structure for {report_type} report. Expected a list of dictionaries or a single dictionary.")

    # Generate Excel file with the report type and date in the filename
    excel_output = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    df.to_excel(excel_output, index=False)

    return excel_output
