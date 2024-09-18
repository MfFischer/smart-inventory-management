from flask import jsonify
from suppliers.models import Supplier


# Example view to get all suppliers
def get_suppliers():
    suppliers = Supplier.query.all()
    return jsonify([supplier.to_dict() for supplier in suppliers])
