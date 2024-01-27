"""empty message

Revision ID: 7d1fe0e58de8
Revises: 
Create Date: 2023-03-24 12:58:49.295920

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d1fe0e58de8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('WebConfig', sa.Column('AndroidAppVersion', sa.Integer(), nullable=True, comment='安卓APP软件版本号'))
    op.add_column('WebConfig', sa.Column('AndroidAppDownloadUrl', sa.String(length=100), nullable=True, comment='安卓APP下载链接'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('WebConfig', 'AndroidAppDownloadUrl')
    op.drop_column('WebConfig', 'AndroidAppVersion')
    # ### end Alembic commands ###
