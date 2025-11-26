from marshmallow import Schema, fields, validate

class AccountsReceivableSchema(Schema):
    id = fields.Int(dump_only=True)
    sale_id = fields.Int(required=True)
    due_date = fields.Date(required=True)
    amount_due = fields.Decimal(required=True, as_string=True)
    status = fields.Str(validate=validate.OneOf(["pending", "partially paid", "paid"]), default="pending")
    notes = fields.Str(allow_none=True)

    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
