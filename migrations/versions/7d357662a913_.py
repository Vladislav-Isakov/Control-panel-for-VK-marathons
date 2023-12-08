"""empty message

Revision ID: 7d357662a913
Revises: 092985c720c5
Create Date: 2023-07-05 03:57:09.388490

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d357662a913'
down_revision = '092985c720c5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('information_about_the_post_with_the_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=True),
    sa.Column('comment_id', sa.Integer(), nullable=True),
    sa.Column('task_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['task_id'], ['status_of_marathon_users_tasks.id'], name=op.f('fk_information_about_the_post_with_the_task_task_id_status_of_marathon_users_tasks')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_information_about_the_post_with_the_task'))
    )
    with op.batch_alter_table('information_about_the_post_with_the_task', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_information_about_the_post_with_the_task_comment_id'), ['comment_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_information_about_the_post_with_the_task_post_id'), ['post_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('information_about_the_post_with_the_task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_information_about_the_post_with_the_task_post_id'))
        batch_op.drop_index(batch_op.f('ix_information_about_the_post_with_the_task_comment_id'))

    op.drop_table('information_about_the_post_with_the_task')
    # ### end Alembic commands ###