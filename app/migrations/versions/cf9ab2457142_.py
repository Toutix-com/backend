"""empty message

Revision ID: cf9ab2457142
Revises: 6d9291e0871b
Create Date: 2024-03-08 15:39:43.897649

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf9ab2457142'
down_revision = '6d9291e0871b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('CategoryID', sa.UUID(), nullable=True))
        batch_op.create_foreign_key(None, 'ticket_categories', ['CategoryID'], ['CategoryID'])
        batch_op.drop_column('Category')

    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('PaymentMethodID',
               existing_type=sa.UUID(),
               type_=sa.String(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.alter_column('PaymentMethodID',
               existing_type=sa.String(),
               type_=sa.UUID(),
               existing_nullable=True)

    with op.batch_alter_table('tickets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Category', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('CategoryID')

    # ### end Alembic commands ###