from inventory_system import db
from datetime import datetime

class ReturnedDamagedItem(db.Model):
    """
    Model representing returned or damaged items in the inventory.
    """
    __tablename__ = 'returned_damaged_items'

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    return_date = db.Column(db.Date, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    inventory = db.relationship('Inventory', backref='returned_damaged_items')
    sale = db.relationship('Sale', backref='returned_damaged_items')
    user = db.relationship('User', backref='returned_damaged_items')

    def __repr__(self):
        return f'<ReturnedDamagedItem {self.id} - Sale ID: {self.sale_id} - Reason: {self.reason}>'
