"""empty message

Revision ID: a1319d7fdcfa
Revises: 5ebc4287e867
Create Date: 2024-03-25 22:44:00.070842

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1319d7fdcfa'
down_revision = '5ebc4287e867'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ticket_categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('max_per_person', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('ticket_categories', schema=None) as batch_op:
        batch_op.drop_column('max_per_person')

    # ### end Alembic commands ###
