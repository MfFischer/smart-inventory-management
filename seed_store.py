from inventory_system import db
from products.models import Product
from suppliers.models import Supplier
from users.models import User
from sales.models import Sale
from inventory.models import Inventory  # Import Inventory model
from permissions.models import Permission
from datetime import datetime
from werkzeug.security import generate_password_hash
from inventory_system import create_app
from passlib.hash import scrypt

# Create the Flask app instance
app = create_app()

def seed_store():
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        db.create_all()

        # Create or update sample hardware products with prices and reorder points
        products_data = [
            {"name": "Hammer",
             "description": "16 oz claw hammer with fiberglass handle",
             "price": 15.99, "reorder_point": 10},
            {"name": "Screwdriver Set",
             "description": "10-piece magnetic screwdriver set with ergonomic handles",
             "price": 20.50, "reorder_point": 15},
            {"name": "Drill",
             "description": "Cordless drill with 18V battery and charger",
             "price": 79.99, "reorder_point": 5},
            {"name": "Saw Blade",
             "description": "10-inch circular saw blade for cutting wood",
             "price": 24.75, "reorder_point": 12},
            {"name": "Paint Brush Set",
             "description": "5-piece paint brush set for all paints and stains",
             "price": 12.99, "reorder_point": 20},
            {"name": "Concrete Mix",
             "description": "50 lb bag of fast-setting concrete mix",
             "price": 8.99, "reorder_point": 30},
            {"name": "Plywood Sheet",
             "description": "4x8 foot sheet of 3/4-inch plywood",
             "price": 45.00, "reorder_point": 8},
            {"name": "Nails",
             "description": "5 lb box of 2-inch galvanized nails",
             "price": 5.50, "reorder_point": 50},
            {"name": "Ladder",
             "description": "6-foot aluminum step ladder",
             "price": 60.00, "reorder_point": 5},
            {"name": "Wrench Set",
             "description": "Metric wrench set, 8 pieces, with storage case",
             "price": 29.99, "reorder_point": 10}
        ]

        for product_data in products_data:
            product = Product.query.filter_by(name=product_data["name"]).first()
            if product:
                # Update existing product
                for key, value in product_data.items():
                    setattr(product, key, value)
            else:
                # Create new product
                product = Product(**product_data)
                db.session.add(product)

        # Create or update sample suppliers
        suppliers_data = [
            {"name": "ToolMaster Supplies",
             "email": "contact@toolmastersupplies.com",
             "phone": "555-1234",
             "address": "123 Industrial Ave, Tooltown, TX"},
            {"name": "Builders Depot",
             "email": "sales@buildersdepot.com",
             "phone": "555-5678",
             "address": "456 Construction Rd, Buildsville, CA"},
            {"name": "Handy Hardware Co.",
             "email": "support@handyhardware.com",
             "phone": "555-9101",
             "address": "789 Hardware Blvd, Workcity, NY"}
        ]

        for supplier_data in suppliers_data:
            supplier = Supplier.query.filter_by(email=supplier_data["email"]).first()
            if supplier:
                # Update existing supplier
                for key, value in supplier_data.items():
                    setattr(supplier, key, value)
            else:
                # Create new supplier
                supplier = Supplier(**supplier_data)
                db.session.add(supplier)

        # Create or update sample permissions
        permissions_data = [
            {"name": 'view_inventory'},
            {"name": 'edit_inventory'},
            {"name": 'view_sales'},
            {"name": 'edit_sales'},
            {"name": 'manage_users'}
        ]

        for permission_data in permissions_data:
            permission = Permission.query.filter_by(name=permission_data["name"]).first()
            if not permission:
                # Create new permission if not exists
                permission = Permission(**permission_data)
                db.session.add(permission)

        db.session.commit()  # Commit to get permission IDs

        # Fetch the created permissions
        view_inventory_perm = Permission.query.filter_by(name='view_inventory').first()
        edit_inventory_perm = Permission.query.filter_by(name='edit_inventory').first()

        # Assign permissions to admin and staff users
        admin_permissions = Permission.query.all()  # Admin has all permissions
        staff_permissions = [view_inventory_perm, edit_inventory_perm]  # Staff has 'view_inventory' and 'edit_inventory' permissions

        # Create or update sample users
        users_data = [
            {"username": "admin",
             "hashed_password": scrypt.hash("adminpassword"),
             "first_name": "Admin",
             "last_name": "User",
             "email": "admin@hardwarestore.com",
             "role": "admin",
             "status": "active"},
            {"username": "john_doe",
             "hashed_password": scrypt.hash("securepassword1"),
             "first_name": "John",
             "last_name": "Doe",
             "email": "john.doe@hardwarestore.com",
             "role": "staff",
             "status": "active"},
            {"username": "jane_smith",
             "hashed_password": scrypt.hash("securepassword2"),
             "first_name": "Jane",
             "last_name": "Smith",
             "email": "jane.smith@hardwarestore.com",
             "role": "staff",
             "status": "active"},
            {"username": "customer1",
             "hashed_password": scrypt.hash("customerpassword"),
             "first_name": "Bob",
             "last_name": "Builder",
             "email": "bob.builder@gmail.com",
             "role": "customer",
             "status": "active"}
        ]

        for user_data in users_data:
            user = User.query.filter_by(username=user_data["username"]).first()
            if not user:
                # Create new user if not exists
                user = User(**user_data)
                db.session.add(user)

        db.session.commit()  # Commit to get user IDs

        # Assign permissions to users
        admin_user = User.query.filter_by(username="admin").first()
        john_user = User.query.filter_by(username="john_doe").first()
        jane_user = User.query.filter_by(username="jane_smith").first()

        # Add permissions to users
        if admin_user and not admin_user.permissions:
            admin_user.permissions.extend(admin_permissions)
        if john_user and not john_user.permissions:
            john_user.permissions.extend(staff_permissions)
        if jane_user and not jane_user.permissions:
            jane_user.permissions.extend(staff_permissions)

        # Create or update sample inventory records
        inventory_data = [
            {"product_id": 1, "supplier_id": 1,
             "sku": "HAMMER-001", "stock_quantity": 100,
             "reorder_threshold": 10, "unit_price": 15.99},
            {"product_id": 2, "supplier_id": 2,
             "sku": "SCREW-002", "stock_quantity": 50,
             "reorder_threshold": 15, "unit_price": 20.50},
            {"product_id": 3, "supplier_id": 2,
             "sku": "DRILL-003", "stock_quantity": 30,
             "reorder_threshold": 5, "unit_price": 79.99}
        ]

        for inv_data in inventory_data:
            inventory = Inventory.query.filter_by(sku=inv_data["sku"]).first()
            if inventory:
                # Update existing inventory
                for key, value in inv_data.items():
                    setattr(inventory, key, value)
            else:
                # Create new inventory
                inventory = Inventory(**inv_data)
                db.session.add(inventory)

        # Create or update sample sales transactions
        sales_data = [
            {"product_id": 1, "quantity": 2,
             "total_price": 31.98,
             "sale_date": datetime.now(),
             "customer_name": "Alice Contractor",
             "sale_status": "completed"},
            {"product_id": 3, "quantity": 1,
             "total_price": 79.99,
             "sale_date": datetime.now(),
             "customer_name": "Bob Builder",
             "sale_status": "completed"},
            {"product_id": 6, "quantity": 5,
             "total_price": 44.95,
             "sale_date": datetime.now(),
             "customer_name": "Charlie Mason",
             "sale_status": "pending"},
            {"product_id": 9, "quantity": 1,
             "total_price": 60.00,
             "sale_date": datetime.now(),
             "customer_name": "Dana Decorator",
             "sale_status": "completed"}
        ]

        for sale_data in sales_data:
            sale = Sale.query.filter_by(product_id=sale_data["product_id"],
                                        customer_name=sale_data["customer_name"]).first()
            if not sale:
                # Create new sale transaction if not exists
                sale = Sale(**sale_data)
                db.session.add(sale)

        # Commit all changes to the database
        db.session.commit()
        print("Hardware store database seeded successfully!")

if __name__ == '__main__':
    seed_store()
