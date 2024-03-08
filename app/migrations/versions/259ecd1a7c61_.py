"""empty message

Revision ID: 259ecd1a7c61
Revises: cf9ab2457142
Create Date: 2024-03-08 16:06:15.531869

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '259ecd1a7c61'
down_revision = 'cf9ab2457142'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('QR_STATUS', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.drop_column('QR_STATUS')

    # ### end Alembic commands ###
