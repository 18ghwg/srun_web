"""empty message

Revision ID: 3cc4df5e51c6
Revises: d6baf227f93d
Create Date: 2023-05-27 17:35:45.421487

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '3cc4df5e51c6'
down_revision = 'd6baf227f93d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('workorder', sa.Column('UserId', sa.Integer(), nullable=False, comment='工单阳光跑userid'))
    op.drop_column('workorder', 'UseUserId')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('workorder', sa.Column('UseUserId', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False, comment='工单阳光跑userid'))
    op.drop_column('workorder', 'UserId')
    # ### end Alembic commands ###