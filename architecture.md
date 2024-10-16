```bash
smart_inventory/
│
├── architecture.md                         # Architecture documentation file
├── conftest.py                             # Manage testing setup
│
├── inventory_system/                       # Flask project folder
│   ├── __init__.py                         # Initializes the Flask app
│   ├── settings.py                         # Project settings (including database, JWT, etc.)
│   ├── urls.py                             # Global URL routing
│   ├── wsgi.py                             # WSGI entry point for production
│   ├── swagger.py                          # swagger api documentation logic
│   ├── routes.py                           # HTML routes for index,dashboard, login and logout
│   └── asgi.py                             # Optional: ASGI entry point if needed
│
├── cron_jobs/                              # Background tasks 
│   ├── daily_reorder_check.sh              # tasks for automating actions
│
├── modules/                                # Business logic modules
│   ├suppliers/                             # Suppliers module
│   │    ├── migrations/                    # Database migrations for suppliers
│   │    ├── models.py                      # Supplier model
│   │    ├── views.py                       # Product API views: Handles CRUD operations
│   │    ├── serializers.py                 # Supplier serializers 
│   │    ├── urls.py                        # Supplier URL routing
│   │    └── tests.py                       # Unit tests for suppliers
│   │
│   ├── products/                           # Products module (newly added)
│   │    ├── migrations/                    # Database migrations for products
│   │    ├── models.py                      # Product model
│   │    ├── check_reorder.py               # Cron Job Script to Check for Reorders
│   │    ├── views.py                       # Product API views: Handles CRUD operations
│   │    ├── serializers.py                 # Product serializers
│   │    ├── urls.py                        # Product URL routing
│   │    └── tests.py                       # Unit tests for products
│   │
│   ├── inventory/                          # Inventory module
│   │   ├── migrations/                     # Database migrations for inventory
│   │   ├── models.py                       # Inventory models
│   │   ├── views.py                        # Inventory API views: Handles CRUD operations
│   │   ├── serializers.py                  # Inventory serializers
│   │   ├── urls.py                         # Inventory URL routing
│   │   └── tests.py                        # Unit tests for inventory
│   │
│   ├── sales/                              # Sales module
│   │   ├── migrations/                     # Database migrations for sales
│   │   ├── models.py                       # Sales models
│   │   ├── views.py                        # Sales API views: Handles CRUD operations
│   │   ├── serializers.py                  # Sales serializers
│   │   ├── urls.py                         # Sales URL routing
│   │   └── tests.py                        # Unit tests for sales
│   ├── users/                              # Optional authentication module
│   │   ├── migrations/                     # Database migrations for users
│   │   ├── models.py                       # User model
│   │   ├── views.py                        # User API views: Handles CRUD operations
│   │   ├── serializers.py                  # User serializers
│   │   ├── urls.py                         # User authentication routes
│   │   └── tests.py                        # Unit tests for authentication
│   │   └── decorators.py                   # for managing roles and permission
│   │
│   ├── permissions/                        # permissions module
│   │   ├── migrations/                     # Database migrations for permissions
│   │   ├── models.py                       # Define permission models and relationships
│   │   ├── views.py                        # Admin views to manage permissions(Optional)
│   │   ├── serializers.py                  # serialize permission data(optional)
│   │   ├── urls.py                         # URL routing
│   │   └── tests.py                        # Unit tests for permissions
│   ├──routes/                              # HTML db table routes module
│      ├── inventory_routes/                # HTML inventory logic route
│      ├── products_routes.py               # HTML products logic route
│      ├── sales_routes.py                  # HTML sales logic route
│      ├── suppliers_routes.py              # HTML suppliers logic route
│      └──  users_routes.py                 # HTML users logic route
│                      
│
│
│
├── app/                                    # Main application directory
│   ├── templates/                          # HTML templates for the frontend
│   │   ├── add_product.html                # Adding product setup
│   │   ├── add_sale.html                   # Adding sale setup
│   │   ├── base.html                       # Base HTML template
│   │   ├── create_inventory_item.html      # creating new inventory setup
│   │   ├── create_supplier.html            # creating new supplier setup
│   │   ├── create_user.html                # creating new user setup
│   │   ├── edit_inventory.html             # Editing inventory record setup
│   │   ├── edit_product.html               # Editing product record setup
│   │   ├── edit_sale.html                  # Editing sale record setup
│   │   ├── edit_supplier.html              # Editing Supplier record setup
│   │   ├── edit_user.html                  # Editing user record setup
│   │   ├── error.html                      # Default redirect page for error
│   │   ├── index.html                      # Main dashboard
│   │   ├── inventory.html                  # inventory page
│   │   ├── login.html                      # Login page
│   │   ├── low_stock_alerts.html           # Low stock notification logic
│   │   ├── product_details.html            # Details page for product
│   │   ├── products.html                   # Complete view of products
│   │   ├── register.html                   # Register new user setup
│   │   ├── reorder_form.html               # product reorder form setup
│   │   ├── supplier_details.html           # Details page for suppliers
│   │   ├── sales.html                      # Sales management page
│   │   ├── users_list.html                 # Complete users list view setup
│   ├── static/                             # Static files (CSS, JS, images)
│   │   ├── css/
│   │   │   ├── main.css                    # Main stylesheet
│   │   ├── js/
│   │   │   ├── main.js                     # Main JavaScript file
│
├── manage.py                               # Flask CLI management script (using Flask-Script or Flask-CLI)
├── seed_store.py                           # for seeding the database
├── requirements.txt                        # Project dependencies
├── Procfile                                # For deployment (Render)
├── .env                                    # Environment variables (JWT secret, database URL, etc.)
├── .gitignore                              # Ignore unnecessary files
└── README.md                               # Project README with overview and setup instructions
```
