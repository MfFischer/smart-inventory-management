from flask import jsonify, request, Blueprint
from suppliers.models import Supplier
from inventory_system import db
from marshmallow import ValidationError
from suppliers.serializers import SupplierSchema

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

from marshmallow import ValidationError
from suppliers.serializers import SupplierSchema

@suppliers_bp.route('/', methods=['POST'])
def create_supplier():
    schema = SupplierSchema()
    try:
        # Validate and deserialize input
        supplier_data = schema.load(request.json)
        # Check if supplier already exists (optional)
        if Supplier.query.filter_by(email=supplier_data['email']).first():
            return jsonify({"error": "A supplier with this email already exists."}), 400

        # Create new supplier
        supplier = Supplier(**supplier_data)
        db.session.add(supplier)
        db.session.commit()
        return jsonify(schema.dump(supplier)), 201
    except ValidationError as err:
        # If validation fails, return 400 with error messages
        return jsonify(err.messages), 400
    except Exception as e:
        # Catch any unexpected errors
        return jsonify({"error": "Unexpected error", "message": str(e)}), 500

@suppliers_bp.route('/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """
    Retrieve a specific supplier by ID.
    Returns 404 if the supplier is not found.
    """
    supplier = Supplier.query.get(supplier_id)
    if not supplier:
        return jsonify({'error': 'Supplier not found'}), 404
    return jsonify(supplier.to_dict()), 200

@suppliers_bp.route('/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """
    Update an existing supplier by ID with the provided data.
    Expects JSON data in the request body.
    """
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.json
    schema = SupplierSchema(partial=True)

    try:
        # Validate and update supplier fields with provided data
        updated_data = schema.load(data)
        for key, value in updated_data.items():
            setattr(supplier, key, value)

        # Commit the updated supplier to the database
        db.session.commit()

        return jsonify(supplier.to_dict()), 200

    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        return jsonify({"error": "Unexpected error", "message": str(e)}), 500


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
