from flask import jsonify, request, render_template, redirect, url_for
from modules.products.models import Product
from modules.suppliers.models import Supplier
from modules.inventory.models import Inventory
from inventory_system import db
from modules.inventory.serializers import InventorySchema
from sqlalchemy.orm import joinedload
from datetime import datetime
from flask_restx import Namespace, Resource

# Define a namespace for the inventory-related API
api = Namespace('inventory', description='Inventory related operations')

# Initialize InventorySchema instances for serialization and deserialization
inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)


# Class-based resource for all inventory items
@api.route('/')
class InventoryList(Resource):
    def get(self):
        """Get all inventory items."""
        try:
            inventory_items = Inventory.query.options(
                joinedload(Inventory.product)
            ).all()
            return render_template('inventory.html', inventory_items=inventory_items)
        except Exception as e:
            print(f"Error fetching inventory items: {e}")
            return render_template('error.html'), 500


# Class-based resource for creating new inventory items
@api.route('/create')
class InventoryCreate(Resource):
    def get(self):
        """Render form to create a new inventory item."""
        products = Product.query.all()
        suppliers = Supplier.query.all()
        return render_template('create_inventory_item.html', products=products, suppliers=suppliers)

    def post(self):
        """Handle creation of a new inventory item."""
        try:
            data = request.form if request.content_type != 'application/json' else request.json

            # Check if a new product or supplier needs to be created
            product_id = self._get_or_create_product(data)
            supplier_id = self._get_or_create_supplier(data)

            # Ensure no duplicate SKU exists
            if Inventory.query.filter_by(sku=data.get('sku')).first():
                error_message = f"An item with SKU '{data.get('sku')}' already exists."
                return self._handle_error(request, error_message, 'create_inventory_item.html')

            # Create and save the inventory item
            new_item = Inventory(
                product_id=product_id,
                supplier_id=supplier_id,
                sku=data.get('sku'),
                stock_quantity=int(data.get('stock_quantity')),
                reorder_threshold=int(data.get('reorder_threshold')),
                unit_price=float(data.get('unit_price'))
            )
            db.session.add(new_item)
            db.session.commit()

            if request.content_type == 'application/json':
                return jsonify(inventory_schema.dump(new_item)), 201
            else:
                return redirect(url_for('inventory.inventory_list'))
        except Exception as e:
            db.session.rollback()
            error_message = f"An error occurred: {str(e)}"
            return self._handle_error(request, error_message, 'create_inventory_item.html')

    def _get_or_create_product(self, data):
        """Helper to create or fetch a product."""
        if data.get('product_id') == 'new':
            new_product = Product(
                name=data.get('new_product_name'),
                description=data.get('new_product_description')
            )
            db.session.add(new_product)
            db.session.flush()
            return new_product.id
        return int(data.get('product_id'))

    def _get_or_create_supplier(self, data):
        """Helper to create or fetch a supplier."""
        if data.get('supplier_id') == 'new':
            new_supplier = Supplier(
                name=data.get('new_supplier_name'),
                contact=data.get('new_supplier_contact')
            )
            db.session.add(new_supplier)
            db.session.flush()
            return new_supplier.id
        return int(data.get('supplier_id'))

    def _handle_error(self, request, error_message, template):
        """Helper to handle form and JSON errors."""
        if request.content_type == 'application/json':
            return jsonify({"error": error_message}), 400
        else:
            return render_template(template, error=error_message)


# Class-based resource for getting, updating, and deleting inventory items
@api.route('/<int:item_id>')
class InventoryItem(Resource):
    def get(self, item_id):
        """Get a single inventory item by ID."""
        item = Inventory.query.get_or_404(item_id)
        return jsonify(inventory_schema.dump(item)), 200

    def put(self, item_id):
        """Update an inventory item by ID."""
        item = Inventory.query.get_or_404(item_id)
        data = request.json

        errors = inventory_schema.validate(data, partial=True)
        if errors:
            return jsonify(errors), 400

        item.product_id = data.get('product_id', item.product_id)
        item.supplier_id = data.get('supplier_id', item.supplier_id)
        item.sku = data.get('sku', item.sku)
        item.stock_quantity = data.get('stock_quantity', item.stock_quantity)
        item.reorder_threshold = data.get('reorder_threshold', item.reorder_threshold)
        item.unit_price = data.get('unit_price', item.unit_price)

        db.session.commit()
        return jsonify(inventory_schema.dump(item)), 200

    def delete(self, item_id):
        """Delete an inventory item by ID."""
        item = Inventory.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('inventory.inventory_list'))


# Class-based resource for inventory-related operations
@api.route('/<int:item_id>/edit')
class InventoryEdit(Resource):
    def get(self, item_id):
        """Render form to edit an inventory item."""
        item = Inventory.query.get_or_404(item_id)
        products = Product.query.all()
        suppliers = Supplier.query.all()
        return render_template('edit_inventory.html', item=item, products=products, suppliers=suppliers)

    def post(self, item_id):
        """Handle the form submission to edit an inventory item."""
        item = Inventory.query.get_or_404(item_id)

        product_id = request.form.get('product_id')
        supplier_id = request.form.get('supplier_id')

        product = Product.query.get(product_id)
        supplier = Supplier.query.get(supplier_id)

        if not product or not supplier:
            return "Invalid product or supplier selected", 400

        item.product_id = product.id
        item.supplier_id = supplier.id
        item.sku = request.form.get('sku')
        item.stock_quantity = request.form.get('stock_quantity')
        item.reorder_threshold = request.form.get('reorder_threshold')
        item.unit_price = request.form.get('unit_price')

        db.session.commit()
        return redirect(url_for('inventory.inventory_list'))


# Class-based resource for low stock alerts
@api.route('/low-stock-alerts')
class LowStockAlerts(Resource):
    def get(self):
        """Display low stock alerts."""
        try:
            low_stock_items = Inventory.query.filter(
                Inventory.stock_quantity <= Inventory.reorder_threshold
            ).all()
            return render_template('low_stock_alerts.html', low_stock_items=low_stock_items)
        except Exception as e:
            print(f"Error fetching low stock alerts: {e}")
            return render_template('error.html'), 500


# Class-based resource for inventory search
@api.route('/search')
class InventorySearch(Resource):
    def get(self):
        """Search for inventory items by product name."""
        search_query = request.args.get('search')
        if search_query:
            inventory_items = Inventory.query.filter(
                Inventory.product.name.ilike(f'%{search_query}%')
            ).all()
        else:
            inventory_items = Inventory.query.all()
        return render_template('inventory.html', inventory_items=inventory_items)


# Class-based resource for reorder operations
@api.route('/<int:item_id>/reorder')
class InventoryReorder(Resource):
    def get(self, item_id):
        """Render reorder form for an inventory item."""
        item = Inventory.query.get_or_404(item_id)
        supplier_email = item.supplier.email if item.supplier else None
        reorder_quantity = item.product.reorder_quantity if item.product else 0
        return render_template('reorder_form.html', item=item, supplier_email=supplier_email, reorder_quantity=reorder_quantity)

    def post(self, item_id):
        """Handle reorder submission."""
        item = Inventory.query.get_or_404(item_id)
        item.last_reordered_at = datetime.now()
        db.session.commit()
        return redirect(url_for('inventory.inventory_list'))
