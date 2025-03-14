"""remove_profile_picture_column

Revision ID: 49ce60bdebc8
Revises: 7f4fa141c91f
Create Date: 2025-03-14 00:57:08.560781

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '49ce60bdebc8'
down_revision = '7f4fa141c91f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('profile_picture')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('profile_picture', sa.VARCHAR(length=500), nullable=True))

    # ### end Alembic commands ###
