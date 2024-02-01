"""empty message

Revision ID: 84830215d86f
Revises: c68bd4bfe744
Create Date: 2023-04-03 20:31:52.684310

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '84830215d86f'
down_revision = 'c68bd4bfe744'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('WxPusher', sa.Column('Time', sa.DateTime(), nullable=True, comment='加入的时间'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('WxPusher', 'Time')
    # ### end Alembic commands ###