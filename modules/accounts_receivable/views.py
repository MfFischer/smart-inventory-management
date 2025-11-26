from flask import jsonify, request
from flask_restx import Namespace, Resource, fields
from inventory_system import db
from modules.accounts_receivable.models import AccountsReceivable
from modules.accounts_receivable.serializers import AccountsReceivableSchema
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError

# Define a namespace for accounts receivable-related API operations
api = Namespace('accounts_receivable', description='Accounts Receivable related operations')

# Initialize the AccountsReceivableSchema for serialization
accounts_receivable_schema = AccountsReceivableSchema()
accounts_receivables_schema = AccountsReceivableSchema(many=True)

# Define the accounts receivable model for API documentation
accounts_receivable_model = api.model('AccountsReceivable', {
    'sale_id': fields.Integer(required=True, description='Sale ID'),
    'due_date': fields.String(required=True, description='Due date for payment (YYYY-MM-DD)'),
    'amount_due': fields.Float(required=True, description='Amount due for the sale'),
    'status': fields.String(description='Payment status (e.g., pending, partially paid)'),
    'notes': fields.String(description='Optional notes regarding the receivable')
})

@api.route('/')
class AccountsReceivableList(Resource):
    @api.doc(responses={200: 'Success', 500: 'Server Error'})
    def get(self):
        """Retrieve all accounts receivable entries"""
        accounts = AccountsReceivable.query.all()
        return accounts_receivables_schema.dump(accounts), 200

    @api.expect(accounts_receivable_model)
    @api.doc(responses={201: 'Created', 400: 'Validation Error', 415: 'Unsupported Media Type', 500: 'Server Error'})
    def post(self):
        """Create a new accounts receivable entry"""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        try:
            data = accounts_receivable_schema.load(request.json)
            new_account = AccountsReceivable(**data)
            db.session.add(new_account)
            db.session.commit()
            return accounts_receivable_schema.dump(new_account), 201
        except ValidationError as err:
            return err.messages, 400
        except SQLAlchemyError as db_err:
            db.session.rollback()
            return {'message': 'Database error occurred. Please try again.'}, 500

@api.route('/<int:account_id>')
class AccountsReceivableItem(Resource):
    @api.doc(responses={200: 'Success', 404: 'Not Found', 500: 'Server Error'})
    def get(self, account_id):
        """Retrieve a specific accounts receivable entry by ID"""
        account = AccountsReceivable.query.get_or_404(account_id)
        return accounts_receivable_schema.dump(account), 200

    @api.expect(accounts_receivable_model)
    @api.doc(responses={200: 'Success', 400: 'Validation Error', 404: 'Not Found', 415: 'Unsupported Media Type', 500: 'Server Error'})
    def put(self, account_id):
        """Update an existing accounts receivable entry by ID"""
        if not request.is_json:
            return {'message': 'Request must be JSON'}, 415

        account = AccountsReceivable.query.get_or_404(account_id)
        try:
            data = accounts_receivable_schema.load(request.json, partial=True)
            for key, value in data.items():
                setattr(account, key, value)
            db.session.commit()
            return accounts_receivable_schema.dump(account), 200
        except ValidationError as err:
            return err.messages, 400
        except SQLAlchemyError as db_err:
            db.session.rollback()
            return {'message': 'Database error occurred. Please try again.'}, 500

    @api.doc(responses={204: 'No Content', 404: 'Not Found', 500: 'Server Error'})
    def delete(self, account_id):
        """Delete an accounts receivable entry by ID"""
        account = AccountsReceivable.query.get_or_404(account_id)
        db.session.delete(account)
        db.session.commit()
        return '', 204
