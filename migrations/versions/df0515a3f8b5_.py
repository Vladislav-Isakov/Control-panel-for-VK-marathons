"""empty message

Revision ID: df0515a3f8b5
Revises: 82aa172f493e
Create Date: 2023-07-21 07:30:58.288879

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df0515a3f8b5'
down_revision = '82aa172f493e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('apscheduler_jobs', schema=None) as batch_op:
        batch_op.alter_column('job_state',
               existing_type=sa.FLOAT(),
               type_=sa.LargeBinary(),
               existing_nullable=True)
        batch_op.alter_column('next_run_time',
               existing_type=sa.BLOB(),
               type_=sa.Float(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('apscheduler_jobs', schema=None) as batch_op:
        batch_op.alter_column('next_run_time',
               existing_type=sa.Float(),
               type_=sa.BLOB(),
               existing_nullable=True)
        batch_op.alter_column('job_state',
               existing_type=sa.LargeBinary(),
               type_=sa.FLOAT(),
               existing_nullable=True)

    # ### end Alembic commands ###