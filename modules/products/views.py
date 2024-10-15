from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from modules.products.models import Product
from modules.products.serializers import ProductSchema
from inventory_system import db
from sqlalchemy.exc import SQLAlchemyError

# Existing setup
api = Namespace('products_api', description='Products API operations')
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

# Define the Product model for Swagger and validation
product_model = api.model('Product', {
    'name': fields.String(required=True, description='Product name'),
    'description': fields.String(required=True, description='Product description'),
    'price': fields.Float(required=True, description='Product price'),
    'quantity_in_stock': fields.Integer(required=True, description='Quantity in stock'),
    'reorder_point': fields.Integer(required=True, description='Reorder point')
})


# ------------------------------
# Existing CRUD API Endpoints
# ------------------------------

@api.route('/api/products')
class ProductAPIList(Resource):
    def get(self):
        """Get all products in JSON format."""
        products = Product.query.all()
        return products_schema.dump(products), 200

    @api.expect(product_model, validate=True)
    def post(self):
        """Create a new product."""
        data = request.json
        try:
            new_product = Product(**data)
            db.session.add(new_product)
            db.session.commit()
            return product_schema.dump(new_product), 201
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500


@api.route('/api/products/<int:product_id>')
class ProductAPI(Resource):
    def get(self, product_id):
        """Get a single product by ID."""
        product = Product.query.get_or_404(product_id)
        return product_schema.dump(product), 200

    @api.expect(product_model, validate=True)
    def put(self, product_id):
        """Update a product by ID."""
        product = Product.query.get_or_404(product_id)
        data = request.json

        for key, value in data.items():
            setattr(product, key, value)

        try:
            db.session.commit()
            return product_schema.dump(product), 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    def delete(self, product_id):
        """Delete a product by ID."""
        product = Product.query.get_or_404(product_id)
        try:
            # Check for associated sales records
            if product.sales:
                return {"error": "Cannot delete a product with associated sales records"}, 400

            db.session.delete(product)
            db.session.commit()
            return {"message": "Product deleted successfully"}, 200
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"error": str(e)}, 500
