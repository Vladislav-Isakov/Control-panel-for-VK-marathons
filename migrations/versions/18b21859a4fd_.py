"""empty message

Revision ID: 18b21859a4fd
Revises: 7d357662a913
Create Date: 2023-07-05 04:03:46.160049

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '18b21859a4fd'
down_revision = '7d357662a913'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('information_about_the_post_with_the_task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_information_about_the_post_with_the_task_user_id_marathon_users'), 'marathon_users', ['user_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('information_about_the_post_with_the_task', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_information_about_the_post_with_the_task_user_id_marathon_users'), type_='foreignkey')
        batch_op.drop_column('user_id')

    # ### end Alembic commands ###
