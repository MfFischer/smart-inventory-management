"""Add description to permissions

Revision ID: 5943fd6ccdae
Revises: c71ed80cf844
Create Date: 2024-09-26 22:40:46.891956

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5943fd6ccdae'
down_revision = 'c71ed80cf844'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('permissions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.String(length=255), nullable=True))

    with op.batch_alter_table('user_permissions', schema=None) as batch_op:
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('permission_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_permissions', schema=None) as batch_op:
        batch_op.alter_column('permission_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    with op.batch_alter_table('permissions', schema=None) as batch_op:
        batch_op.drop_column('description')

    # ### end Alembic commands ###