"""empty message

Revision ID: bbc5e6d9dec0
Revises: 3cc4df5e51c6
Create Date: 2023-05-27 17:36:25.301934

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'bbc5e6d9dec0'
down_revision = '3cc4df5e51c6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Workorder',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('User', sa.String(length=100), nullable=False, comment='网站账号'),
    sa.Column('AdminUser', sa.String(length=50), nullable=False, comment='上级用户名'),
    sa.Column('UserId', sa.Integer(), nullable=False, comment='工单阳光跑userid'),
    sa.Column('WorkContent', sa.String(length=255), nullable=False, comment='工单内容'),
    sa.Column('Time', sa.DateTime(), nullable=False, comment='创建工单的时间'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    op.drop_index('id', table_name='workorder')
    op.drop_table('workorder')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('workorder',
    sa.Column('id', mysql.INTEGER(display_width=11), autoincrement=True, nullable=False),
    sa.Column('User', mysql.VARCHAR(length=100), nullable=False, comment='网站账号'),
    sa.Column('AdminUser', mysql.VARCHAR(length=50), nullable=False, comment='上级用户名'),
    sa.Column('WorkContent', mysql.VARCHAR(length=255), nullable=False, comment='工单内容'),
    sa.Column('Time', mysql.DATETIME(), nullable=False, comment='创建工单的时间'),
    sa.Column('UserId', mysql.INTEGER(display_width=11), autoincrement=False, nullable=False, comment='工单阳光跑userid'),
    sa.PrimaryKeyConstraint('id'),
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    op.create_index('id', 'workorder', ['id'], unique=False)
    op.drop_table('Workorder')
    # ### end Alembic commands ###
