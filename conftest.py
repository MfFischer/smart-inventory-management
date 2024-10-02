import pytest
from inventory_system import db
from modules.products.models import Product
from modules.suppliers.models import Supplier
from modules.users.models import User
from modules.sales import Sale
from datetime import datetime
from inventory_system import create_app
from werkzeug.security import generate_password_hash

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
    products = [
        Product(
            name="Hammer",
            description="16 oz claw hammer with fiberglass handle",
            price=15.99,
            reorder_point=10
        ),
        Product(
            name="Screwdriver Set",
            description="10-piece magnetic screwdriver set with ergonomic handles",
            price=20.50,
            reorder_point=15
        ),
        Product(
            name="Drill",
            description="Cordless drill with 18V battery and charger",
            price=79.99,
            reorder_point=5
        ),
        Product(
            name="Saw Blade",
            description="10-inch circular saw blade for cutting wood",
            price=24.75,
            reorder_point=12
        ),
        Product(
            name="Paint Brush Set",
            description="5-piece paint brush set for all paints and stains",
            price=12.99,
            reorder_point=20
        ),
        Product(
            name="Concrete Mix",
            description="50 lb bag of fast-setting concrete mix",
            price=8.99,
            reorder_point=30
        ),
        Product(
            name="Plywood Sheet",
            description="4x8 foot sheet of 3/4-inch plywood",
            price=45.00,
            reorder_point=8
        ),
        Product(
            name="Nails",
            description="5 lb box of 2-inch galvanized nails",
            price=5.50,
            reorder_point=50
        ),
        Product(
            name="Ladder",
            description="6-foot aluminum step ladder",
            price=60.00,
            reorder_point=5
        ),
        Product(
            name="Wrench Set",
            description="Metric wrench set, 8 pieces, with storage case",
            price=29.99,
            reorder_point=10
        )
    ]
    db.session.add_all(products)

    # Create sample suppliers
    suppliers = [
        Supplier(
            name="ToolMaster Supplies",
            email="contact@toolmastersupplies.com",
            phone="555-1234",
            address="123 Industrial Ave, Tooltown, TX"
        ),
        Supplier(
            name="Builders Depot",
            email="sales@buildersdepot.com",
            phone="555-5678",
            address="456 Construction Rd, Buildsville, CA"
        ),
        Supplier(
            name="Handy Hardware Co.",
            email="support@handyhardware.com",
            phone="555-9101",
            address="789 Hardware Blvd, Workcity, NY"
        )
    ]
    db.session.add_all(suppliers)

    # Create sample users (staff and customers)
    users = [
        User(
            username="admin",
            hashed_password=generate_password_hash("adminpassword"),
            first_name="Admin",
            last_name="User",
            email="admin@hardwarestore.com",
            role="admin",
            status="active"
        ),
        User(
            username="john_doe",
            hashed_password=generate_password_hash("securepassword1"),
            first_name="John",
            last_name="Doe",
            email="john.doe@hardwarestore.com",
            role="staff",
            status="active"
        ),
        User(
            username="jane_smith",
            hashed_password=generate_password_hash("securepassword2"),
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@hardwarestore.com",
            role="staff",
            status="active"
        ),
        User(
            username="customer1",
            hashed_password=generate_password_hash("customerpassword"),
            first_name="Bob",
            last_name="Builder",
            email="bob.builder@gmail.com",
            role="customer",
            status="active"
        )
    ]
    db.session.add_all(users)

    # Create sample sales transactions
    sales = [
        Sale(
            product_id=1,  # Hammer
            quantity=2,
            total_price=products[0].price * 2,
            sale_date=datetime.utcnow(),
            customer_name="Alice Contractor"
        ),
        Sale(
            product_id=3,  # Drill
            quantity=1,
            total_price=products[2].price,
            sale_date=datetime.utcnow(),
            customer_name="Bob Builder"
        ),
        Sale(
            product_id=6,  # Concrete Mix
            quantity=5,
            total_price=products[5].price * 5,
            sale_date=datetime.utcnow(),
            customer_name="Charlie Mason"
        ),
        Sale(
            product_id=9,  # Ladder
            quantity=1,
            total_price=products[8].price,
            sale_date=datetime.utcnow(),
            customer_name="Dana Decorator"
        )
    ]
    db.session.add_all(sales)

    # Commit all changes to the database
    db.session.commit()
    print("Store database seeded successfully!")