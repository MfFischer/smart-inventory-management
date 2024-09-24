"""Add quantity_in_stock and reorder_quantity fields to Product model

Revision ID: d97175f4d24e
Revises: 429445e0cd6c
Create Date: 2024-09-23 14:18:21.862671

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# Revision identifiers, used by Alembic.
revision = 'd97175f4d24e'
down_revision = '429445e0cd6c'
branch_labels = None
depends_on = None

def upgrade():
    # Get the current dialect to check if it's SQLite
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Create an inspector to check the existing columns in the 'products' table
    inspector = inspect(op.get_bind())
    columns = [column['name'] for column in inspector.get_columns('products')]

    # Check and add the column 'quantity_in_stock' if it doesn't already exist
    if 'quantity_in_stock' not in columns:
        with op.batch_alter_table('products') as batch_op:
            batch_op.add_column(sa.Column('quantity_in_stock', sa.Integer(), nullable=False, server_default='0'))

    # Check and add the column 'reorder_quantity' if it doesn't already exist
    if 'reorder_quantity' not in columns:
        with op.batch_alter_table('products') as batch_op:
            batch_op.add_column(sa.Column('reorder_quantity', sa.Integer(), nullable=False, server_default='0'))

    # Remove the server default only if the dialect is not SQLite
    if dialect != 'sqlite':
        op.alter_column('products', 'quantity_in_stock', server_default=None)
        op.alter_column('products', 'reorder_quantity', server_default=None)

def downgrade():
    # Get the current dialect to check if it's SQLite
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Remove columns if they exist
    inspector = inspect(op.get_bind())
    columns = [column['name'] for column in inspector.get_columns('products')]

    with op.batch_alter_table('products') as batch_op:
        if 'quantity_in_stock' in columns:
            batch_op.drop_column('quantity_in_stock')
        if 'reorder_quantity' in columns:
            batch_op.drop_column('reorder_quantity')
