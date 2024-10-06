from flask import jsonify, request
from flask_restx import Namespace, Resource
from inventory_system import db
from modules.suppliers.models import Supplier
from modules.suppliers.serializers import SupplierSchema
from marshmallow import ValidationError

# Define a namespace for supplier-related API operations
api = Namespace('suppliers', description='Suppliers related operations')

# Initialize the SupplierSchema for serialization
supplier_schema = SupplierSchema()
suppliers_schema = SupplierSchema(many=True)

@api.route('/')
class SupplierList(Resource):
    def get(self):
        """Retrieve all suppliers from the database (JSON)."""
        suppliers = Supplier.query.all()
        return jsonify(suppliers_schema.dump(suppliers)), 200

@api.route('/<int:supplier_id>')
class SupplierDetail(Resource):
    def get(self, supplier_id):
        """Retrieve a specific supplier by ID (JSON)."""
        supplier = Supplier.query.get_or_404(supplier_id)
        return jsonify(supplier_schema.dump(supplier)), 200

    def put(self, supplier_id):
        """Update an existing supplier by ID (JSON)."""
        supplier = Supplier.query.get_or_404(supplier_id)
        schema = SupplierSchema(partial=True)
        try:
            supplier_data = schema.load(request.json)
            for key, value in supplier_data.items():
                setattr(supplier, key, value)
            db.session.commit()
            return jsonify(supplier_schema.dump(supplier)), 200
        except ValidationError as err:
            return jsonify(err.messages), 400

    def delete(self, supplier_id):
        """Delete a supplier by ID (JSON)."""
        supplier = Supplier.query.get_or_404(supplier_id)
        db.session.delete(supplier)
        db.session.commit()
        return '', 204

@api.route('/api_search')
class SupplierAPISearch(Resource):
    def get(self):
        """Search suppliers by name (JSON)."""
        query = request.args.get('q', '')
        suppliers = Supplier.query.filter(Supplier.name.ilike(f'%{query}%')).all()
        return jsonify(suppliers_schema.dump(suppliers)), 200

