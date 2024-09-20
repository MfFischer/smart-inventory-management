from flask import jsonify, request, Blueprint
from suppliers.models import Supplier
from inventory_system import db

# Create a blueprint for supplier-related routes
suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/', methods=['GET'])
def get_suppliers():
    """
    Retrieve all suppliers from the database.
    Returns a JSON list of supplier dictionaries.
    """
    suppliers = Supplier.query.all()
    # Convert supplier objects to dictionaries and return as JSON
    return jsonify([supplier.to_dict() for supplier in suppliers]), 200

@suppliers_bp.route('/', methods=['POST'])
def create_supplier():
    """
    Create a new supplier with the provided data.
    Expects JSON data in the request body.
    """
    data = request.json

    # Create a new Supplier object using provided data
    new_supplier = Supplier(
        name=data.get('name'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address')
    )

    # Add and commit the new supplier to the database
    db.session.add(new_supplier)
    db.session.commit()

    # Return the newly created supplier as a JSON response
    return jsonify(new_supplier.to_dict()), 201

@suppliers_bp.route('/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """
    Update an existing supplier by ID with the provided data.
    Expects JSON data in the request body.
    """
    # Retrieve supplier by ID or return 404 if not found
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.json

    # Update supplier fields with provided data, defaulting to existing values if not provided
    supplier.name = data.get('name', supplier.name)
    supplier.phone = data.get('phone', supplier.phone)
    supplier.email = data.get('email', supplier.email)
    supplier.address = data.get('address', supplier.address)

    # Commit the updated supplier to the database
    db.session.commit()

    # Return the updated supplier as a JSON response
    return jsonify(supplier.to_dict()), 200

@suppliers_bp.route('/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    """
    Delete an existing supplier by ID.
    """
    # Retrieve supplier by ID or return 404 if not found
    supplier = Supplier.query.get_or_404(supplier_id)

    # Delete the supplier from the database
    db.session.delete(supplier)
    db.session.commit()

    # Return no content to indicate successful deletion
    return '', 204
