from flask import jsonify, request
from flask_restx import Namespace, Resource, fields
from inventory_system import db
from modules.expenses.models import Expense, Category
from datetime import datetime

api = Namespace('expenses', description='Expense management operations')

# Define the model for API documentation
expense_model = api.model('Expense', {
    'user_id': fields.Integer(required=True, description='User ID'),
    'expense_type': fields.String(required=True, description='Type of Expense'),
    'description': fields.String(description='Expense description'),
    'amount': fields.Float(required=True, description='Expense amount'),
    'date_incurred': fields.DateTime(description='Date expense was incurred')
})

category_model = api.model('Category', {
    'user_id': fields.Integer(required=True, description='User ID'),
    'name': fields.String(required=True, description='Category name'),
    'description': fields.String(description='Category description')
})

@api.route('/')
class ExpenseList(Resource):
    @api.marshal_list_with(expense_model)
    def get(self):
        """Retrieve all expenses for a specific user."""
        user_id = request.args.get('user_id')
        expenses = Expense.query.filter_by(user_id=user_id).all()
        return expenses

    @api.expect(expense_model)
    def post(self):
        """Create a new expense entry."""
        data = request.json
        new_expense = Expense(
            user_id=data['user_id'],
            expense_type=data['expense_type'],
            description=data.get('description'),
            amount=data['amount'],
            date_incurred=data.get('date_incurred', datetime.now())
        )
        db.session.add(new_expense)
        db.session.commit()
        return jsonify(new_expense.to_dict()), 201

@api.route('/<int:expense_id>')
class ExpenseDetail(Resource):
    @api.marshal_with(expense_model)
    def get(self, expense_id):
        """Retrieve a specific expense by ID."""
        expense = Expense.query.get_or_404(expense_id)
        return expense

    @api.expect(expense_model)
    def put(self, expense_id):
        """Update an existing expense by ID."""
        expense = Expense.query.get_or_404(expense_id)
        data = request.json
        expense.expense_type = data.get('expense_type', expense.expense_type)
        expense.description = data.get('description', expense.description)
        expense.amount = data.get('amount', expense.amount)
        expense.date_incurred = data.get('date_incurred', expense.date_incurred)
        db.session.commit()
        return jsonify(expense.to_dict())

    def delete(self, expense_id):
        """Delete an expense by ID."""
        expense = Expense.query.get_or_404(expense_id)
        db.session.delete(expense)
        db.session.commit()
        return '', 204

@api.route('/')
class CategoryList(Resource):
    @api.marshal_list_with(category_model)
    def get(self):
        """Retrieve all categories for a specific user."""
        user_id = request.args.get('user_id')
        categories = Category.query.filter_by(user_id=user_id).all()
        return categories

    @api.expect(category_model)
    def post(self):
        """Create a new category."""
        data = request.json
        new_category = Category(
            user_id=data['user_id'],
            name=data['name'],
            description=data.get('description')
        )
        db.session.add(new_category)
        db.session.commit()
        return jsonify(new_category.to_dict()), 201
