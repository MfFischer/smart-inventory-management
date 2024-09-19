from flask import jsonify, request, Blueprint
from suppliers.models import Supplier
from inventory_system import db

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    suppliers = Supplier.query.all()
    return jsonify([supplier.to_dict() for supplier in suppliers]), 200

@suppliers_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    data = request.json
    new_supplier = Supplier(
        name=data.get('name'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address')
    )
    db.session.add(new_supplier)
    db.session.commit()
    return jsonify(new_supplier.to_dict()), 201

@suppliers_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.json
    supplier.name = data.get('name', supplier.name)
    supplier.phone = data.get('phone', supplier.phone)
    supplier.email = data.get('email', supplier.email)
    supplier.address = data.get('address', supplier.address)
    db.session.commit()
    return jsonify(supplier.to_dict()), 200

@suppliers_bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    db.session.delete(supplier)
    db.session.commit()
    return '', 204
