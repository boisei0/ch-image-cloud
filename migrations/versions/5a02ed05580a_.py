"""empty message

Revision ID: 5a02ed05580a
Revises: 
Create Date: 2018-05-29 16:28:25.009257

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a02ed05580a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('show_nsfw', sa.Boolean(), default=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'show_nsfw')
    # ### end Alembic commands ###
