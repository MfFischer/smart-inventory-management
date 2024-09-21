# conftest.py
import pytest
from inventory_system import db, create_app
from products.models import Product
from suppliers.models import Supplier
from sales.models import Sale
from inventory.models import Inventory
from users.models import User
from decimal import Decimal

@pytest.fixture(scope='module')

def test_client():
    """
    Set up the Flask test client for the module scope.
    Creates a temporary in-memory SQLite database for testing.
    """
    # Create the Flask application configured for testing
    flask_app = create_app()
    flask_app.config.from_object('inventory_system.settings')
    flask_app.config['TESTING'] = True  # Enable testing mode
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory SQLite database

    # Create a test client using the Flask application configured above
    testing_client = flask_app.test_client()

    # Establish an application context before running the tests
    ctx = flask_app.app_context()
    ctx.push()

    # Create the database and the database table(s)
    db.create_all()

    # Seed the database with realistic data
    seed_database()
    # this is where the testing happens!
    yield testing_client

    # Cleanup: Drop all data after tests
    db.session.remove()
    db.drop_all()
    ctx.pop()


def seed_database():
    """
    Seed the database with initial data for testing.
    """
    # Create sample products with prices
    product1 = Product(
        name="Product 1",
        description="High quality product",
        price=20.50
    )
    product2 = Product(
        name="Product 2",
        description="Affordable product",
        price='10.00'
    )

    # Create sample suppliers
    supplier1 = Supplier(
        name="Supplier 1",
        email="supplier1@example.com",
        phone="1234567890",
        address="123 Supplier Street"
    )
    supplier2 = Supplier(
        name="Supplier 2",
        email="supplier2@example.com",
        phone="0987654321",
        address="456 Supplier Avenue"
    )

    # Create sample sales
    sale1 = Sale(
        product_id=1,
        quantity=10,
        total_price="205.00",
        sale_status="completed"
    )
    sale2 = Sale(
        product_id=2,
        quantity=5,
        total_price="50.00",
        sale_status="pending"
    )

    # Create sample inventory
    inventory1 = Inventory(
        product_id=1,
        supplier_id=1,
        sku="SKU001",
        stock_quantity=100,
        reorder_threshold=10,
        unit_price=15.00
    )
    inventory2 = Inventory(
        product_id=2,
        supplier_id=2,
        sku="SKU002",
        stock_quantity=200,
        reorder_threshold=20,
        unit_price=8.00
    )

    # Create sample users
    user1 = User(
        username="admin",
        hashed_password="adminpass",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        role="admin",
        status="active"
    )
    user2 = User(
        username="staff",
        hashed_password="staffpass",
        first_name="Staff",
        last_name="Member",
        email="staff@example.com",
        role="staff",
        status="active"
    )

    # Add all entities to the session
    db.session.add_all([product1, product2, supplier1, supplier2, sale1, sale2, inventory1, inventory2, user1, user2])

    # Commit the session
    db.session.commit()
