"""Add quantity_in_stock and reorder_quantity fields to Product model

Revision ID: d97175f4d24e
Revises: 429445e0cd6c
Create Date: 2024-09-23 14:18:21.862671

"""
from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = 'd97175f4d24e'
down_revision = '429445e0cd6c'
branch_labels = None
depends_on = None

def upgrade():
    # Add columns with default values for existing rows
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('quantity_in_stock', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('reorder_quantity', sa.Integer(), nullable=False, server_default='0'))

    # Remove the server default (optional, only if you don't want to keep it)
    op.alter_column('products', 'quantity_in_stock', server_default=None)
    op.alter_column('products', 'reorder_quantity', server_default=None)

def downgrade():
    # Downgrade logic to remove the columns
    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_column('quantity_in_stock')
        batch_op.drop_column('reorder_quantity')

    # ### end Alembic commands ###
