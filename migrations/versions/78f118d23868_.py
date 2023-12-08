"""empty message

Revision ID: 78f118d23868
Revises: 3baf050a3624
Create Date: 2023-06-23 17:11:38.630448

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78f118d23868'
down_revision = '3baf050a3624'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('presence_of_sheet_linked_to_group_in_the_table',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('availability', sa.Boolean(), nullable=True),
    sa.Column('setting_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['setting_id'], ['table_column_settings.id'], name=op.f('fk_presence_of_sheet_linked_to_group_in_the_table_setting_id_table_column_settings')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_presence_of_sheet_linked_to_group_in_the_table'))
    )
    op.create_table('name_of_the_sheet_linked_to_group_in_the_table',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('word', sa.String(length=128), nullable=True),
    sa.Column('sheet_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['sheet_id'], ['presence_of_sheet_linked_to_group_in_the_table.id'], name=op.f('fk_name_of_the_sheet_linked_to_group_in_the_table_sheet_id_presence_of_sheet_linked_to_group_in_the_table')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_name_of_the_sheet_linked_to_group_in_the_table'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('name_of_the_sheet_linked_to_group_in_the_table')
    op.drop_table('presence_of_sheet_linked_to_group_in_the_table')
    # ### end Alembic commands ###
