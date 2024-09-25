from inventory_system import db
from products.models import Product
from suppliers.models import Supplier
from users.models import User
from sales.models import Sale
from permissions.models import Permission  # Import the Permission model
from datetime import datetime
from werkzeug.security import generate_password_hash
from inventory_system import create_app

# Create the Flask app instance
app = create_app()

def seed_store():
    # Create sample hardware products with prices and reorder points
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

    # Create sample permissions
    permissions = [
        Permission(name='view_inventory'),
        Permission(name='edit_inventory'),
        Permission(name='view_sales'),
        Permission(name='edit_sales'),
        Permission(name='manage_users')
    ]
    db.session.add_all(permissions)
    db.session.commit()  # Commit to get permission IDs

    # Assign permissions to admin and staff users
    admin_permissions = permissions  # Admin has all permissions
    staff_permissions = permissions[:2]  # Staff has 'view_inventory' and 'edit_inventory' permissions

    # Create sample users (staff and customers)
    users = [
        User(
            username="admin",
            hashed_password=generate_password_hash("adminpassword"),
            first_name="Admin",
            last_name="User",
            email="admin@hardwarestore.com",
            role="admin",
            status="active",
            permissions=admin_permissions  # Assign all permissions to admin
        ),
        User(
            username="john_doe",
            hashed_password=generate_password_hash("securepassword1"),
            first_name="John",
            last_name="Doe",
            email="john.doe@hardwarestore.com",
            role="staff",
            status="active",
            permissions=staff_permissions  # Assign inventory permissions to staff
        ),
        User(
            username="jane_smith",
            hashed_password=generate_password_hash("securepassword2"),
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@hardwarestore.com",
            role="staff",
            status="active",
            permissions=staff_permissions  # Assign inventory permissions to staff
        ),
        User(
            username="customer1",
            hashed_password=generate_password_hash("customerpassword"),
            first_name="Bob",
            last_name="Builder",
            email="bob.builder@gmail.com",
            role="customer",
            status="active"  # No special permissions for customers
        )
    ]
    db.session.add_all(users)

    # Create sample sales transactions
    sales = [
        Sale(
            product_id=1,  # Hammer
            quantity=2,
            total_price=products[0].price * 2,
            sale_date=datetime.now(),
            customer_name="Alice Contractor",
            sale_status = "completed"
        ),
        Sale(
            product_id=3,  # Drill
            quantity=1,
            total_price=products[2].price,
            sale_date=datetime.now(),
            customer_name="Bob Builder",
            sale_status = "completed"
        ),
        Sale(
            product_id=6,  # Concrete Mix
            quantity=5,
            total_price=products[5].price * 5,
            sale_date=datetime.now(),
            customer_name="Charlie Mason",
            sale_status="pending"
        ),
        Sale(
            product_id=9,  # Ladder
            quantity=1,
            total_price=products[8].price,
            sale_date=datetime.now(),
            customer_name="Dana Decorator",
            sale_status="completed"
        )
    ]
    db.session.add_all(sales)

    # Commit all changes to the database
    db.session.commit()
    print("Hardware store database seeded successfully!")

if __name__ == '__main__':
    # Run the seeding function within the application context
    with app.app_context():
        seed_store()
