import sys
import os

# Add the root directory of the project to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from products.models import Product
from inventory_system import create_app
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reorder_log.log'),   # Log to file
        logging.StreamHandler()                  # Log to console
    ]
)

# Create Flask app context
app = create_app()
app.app_context().push()

def check_reorder():
    # Query products that are below the reorder point
    products_to_reorder = Product.query.filter(Product.quantity_in_stock <= Product.reorder_point).all()

    if products_to_reorder:
        message = "The following products are below the reorder point:\n"
        for product in products_to_reorder:
            message += (f"Product ID: {product.id}, Name: {product.name}, "
                        f"Current Stock: {product.quantity_in_stock}, "
                        f"Reorder Point: {product.reorder_point}, "
                        f"Reorder Quantity: {product.reorder_quantity}\n")

        # Log the information
        logging.info(message)

        # Log the check
        logging.info("Reorder check completed.")
    else:
        logging.info("No products need reordering.")

if __name__ == "__main__":
    check_reorder()
