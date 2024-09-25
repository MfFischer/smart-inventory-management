"""Update permissions and user_permissions models

Revision ID: ec56c96e30c1
Revises: 7b0cd4b46d7c
Create Date: 2024-09-25 20:58:17.502209

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


# revision identifiers, used by Alembic.
revision = 'ec56c96e30c1'
down_revision = '7b0cd4b46d7c'
branch_labels = None
depends_on = None


def column_exists(conn, table_name, column_name):
    inspector = reflection.Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    conn = op.get_bind()

    # Check and create 'inventory_movements' table if it doesn't exist
    if not conn.dialect.has_table(conn, 'inventory_movements'):
        op.create_table('inventory_movements',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('movement_type', sa.String(length=50), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'], name='fk_inventory_movements_product_id'), # Added name for the foreign key constraint
            sa.PrimaryKeyConstraint('id')
        )

    # Check and add 'supplier_id' column to 'products' table if it doesn't exist
    if not column_exists(conn, 'products', 'supplier_id'):
        with op.batch_alter_table('products', schema=None) as batch_op:
            batch_op.add_column(sa.Column('supplier_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                constraint_name='fk_products_supplier_id',  # Add a name to the foreign key
                referent_table='suppliers',
                local_cols=['supplier_id'],
                remote_cols=['id']
            )

    # Check and add 'contact_info' column to 'suppliers' table if it doesn't exist
    if not column_exists(conn, 'suppliers', 'contact_info'):
        with op.batch_alter_table('suppliers', schema=None) as batch_op:
            batch_op.add_column(sa.Column('contact_info', sa.Text(), nullable=True))

def downgrade():
    conn = op.get_bind()

    # Remove 'contact_info' column from 'suppliers' table if it exists
    if column_exists(conn, 'suppliers', 'contact_info'):
        with op.batch_alter_table('suppliers', schema=None) as batch_op:
            batch_op.drop_column('contact_info')

    # Remove the foreign key constraint and 'supplier_id' column from 'products' table if it exists
    if column_exists(conn, 'products', 'supplier_id'):
        with op.batch_alter_table('products', schema=None) as batch_op:
            batch_op.drop_constraint('fk_products_supplier_id', type_='foreignkey')
            batch_op.drop_column('supplier_id')

    # Drop 'inventory_movements' table if it exists
    if conn.dialect.has_table(conn, 'inventory_movements'):
        op.drop_table('inventory_movements')
