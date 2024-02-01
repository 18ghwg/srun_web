"""empty message

Revision ID: 835ba67af8df
Revises: ba66dfe29823
Create Date: 2023-09-12 14:24:37.856285

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '835ba67af8df'
down_revision = 'ba66dfe29823'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('NRunIMEICodes', 'State',
               existing_type=mysql.TINYINT(display_width=1),
               comment='IMEICode状态，1有效',
               existing_comment='IMEICode状态，正逻辑',
               existing_nullable=False)
    op.alter_column('WebConfig', 'WebSwitch',
               existing_type=mysql.TINYINT(display_width=1),
               comment='网站全局开关0关闭1打开',
               existing_comment='网站全局开关',
               existing_nullable=False)
    op.alter_column('Workorder', 'State',
               existing_type=mysql.TINYINT(display_width=1),
               comment='工单状态,0待回复1已回复2关闭',
               existing_comment='工单状态',
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Workorder', 'State',
               existing_type=mysql.TINYINT(display_width=1),
               comment='工单状态',
               existing_comment='工单状态,0待回复1已回复2关闭',
               existing_nullable=False)
    op.alter_column('WebConfig', 'WebSwitch',
               existing_type=mysql.TINYINT(display_width=1),
               comment='网站全局开关',
               existing_comment='网站全局开关0关闭1打开',
               existing_nullable=False)
    op.alter_column('NRunIMEICodes', 'State',
               existing_type=mysql.TINYINT(display_width=1),
               comment='IMEICode状态，正逻辑',
               existing_comment='IMEICode状态，1有效',
               existing_nullable=False)
    # ### end Alembic commands ###