from flask import jsonify, request
from flask_restx import Namespace, Resource, fields
from inventory_system import db
from modules.suppliers.models import Supplier
from modules.suppliers.serializers import SupplierSchema
from marshmallow import ValidationError

# Define a namespace for supplier-related API operations
api = Namespace('suppliers', description='Suppliers related operations')

# Initialize the SupplierSchema for serialization
supplier_schema = SupplierSchema()
suppliers_schema = SupplierSchema(many=True)

supplier_model = api.model('Supplier', {
    'name': fields.String(required=True, description='Supplier name'),
    'contact_person': fields.String(required=True, description='Contact person name'),
    'email': fields.String(required=True, description='Supplier email'),
    'phone': fields.String(required=True, description='Supplier phone number'),
    'address': fields.String(required=True, description='Supplier address')
})

@api.route('/')
class SupplierList(Resource):
    @api.doc(responses={200: 'Success',
                        500: 'Server Error'})
    def get(self):
        """Retrieve all suppliers"""
        suppliers = Supplier.query.all()
        return suppliers_schema.dump(suppliers), 200

    @api.expect(supplier_model)
    @api.doc(responses={201: 'Created',
                        400: 'Validation Error',
                        500: 'Server Error'})
    def post(self):
        """Create a new supplier"""
        try:
            supplier_data = supplier_schema.load(request.json)
            new_supplier = Supplier(**supplier_data)
            db.session.add(new_supplier)
            db.session.commit()
            return supplier_schema.dump(new_supplier), 201
        except ValidationError as err:
            return err.messages, 400

@api.route('/<int:supplier_id>')
class SupplierDetail(Resource):
    @api.doc(responses={200: 'Success',
                        404: 'Not Found',
                        500: 'Server Error'})
    def get(self, supplier_id):
        """Retrieve a specific supplier by ID"""
        supplier = Supplier.query.get_or_404(supplier_id)
        return supplier_schema.dump(supplier), 200

    @api.expect(supplier_model)
    @api.doc(responses={200: 'Success',
                        400: 'Validation Error',
                        404: 'Not Found',
                        500: 'Server Error'})
    def put(self, supplier_id):
        """Update an existing supplier by ID"""
        supplier = Supplier.query.get_or_404(supplier_id)
        try:
            supplier_data = supplier_schema.load(request.json, partial=True)
            for key, value in supplier_data.items():
                setattr(supplier, key, value)
            db.session.commit()
            return supplier_schema.dump(supplier), 200
        except ValidationError as err:
            return err.messages, 400

    @api.doc(responses={204: 'No Content',
                        404: 'Not Found',
                        500: 'Server Error'})
    def delete(self, supplier_id):
        """Delete a supplier by ID"""
        supplier = Supplier.query.get_or_404(supplier_id)
        db.session.delete(supplier)
        db.session.commit()
        return '', 204

@api.route('/<int:supplier_id>')
class SupplierDetail(Resource):
    def get(self, supplier_id):
        """Retrieve a specific supplier by ID (JSON)."""
        supplier = Supplier.query.get_or_404(supplier_id)
        return jsonify(supplier_schema.dump(supplier)), 200

    @api.expect(supplier_model)
    @api.doc(responses={200: 'Success',
                        400: 'Validation Error',
                        404: 'Not Found',
                        415: 'Unsupported Media Type',
                        500: 'Server Error'})
    def put(self, supplier_id):
        """Update an existing supplier by ID"""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        supplier = Supplier.query.get_or_404(supplier_id)
        try:
            supplier_data = supplier_schema.load(request.json, partial=True)
            for key, value in supplier_data.items():
                setattr(supplier, key, value)
            db.session.commit()
            return supplier_schema.dump(supplier), 200
        except ValidationError as err:
            return err.messages, 400

    def delete(self, supplier_id):
        """Delete a supplier by ID (JSON)."""
        supplier = Supplier.query.get_or_404(supplier_id)
        db.session.delete(supplier)
        db.session.commit()
        return '', 204

@api.route('/api_search')
class SupplierAPISearch(Resource):
    @api.doc(params={'q': 'Search query'},
             responses={200: 'Success',
                        500: 'Server Error'})
    def get(self):
        """Search suppliers by name"""
        query = request.args.get('q', '')
        suppliers = Supplier.query.filter(Supplier.name.ilike(f'%{query}%')).all()
        return suppliers_schema.dump(suppliers), 200

