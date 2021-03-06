"""Adds the postmaster_admins and postmaster_configuration tables

Revision ID: e8f52e92abd0
Revises: bcc85aaa7896
Create Date: 2016-07-13 18:49:32.032805

"""

# revision identifiers, used by Alembic.
revision = 'e8f52e92abd0'
down_revision = 'bcc85aaa7896'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('postmaster_admins',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=True),
    sa.Column('username', sa.String(length=120), nullable=True),
    sa.Column('password', sa.String(length=64), nullable=True),
    sa.Column('source', sa.String(length=64), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('postmaster_configuration',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('setting', sa.String(length=128), nullable=True),
    sa.Column('value', sa.String(length=512), nullable=True),
    sa.Column('regex', sa.String(length=256), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('setting')
    )


def downgrade():
    op.drop_table('postmaster_configuration')
    op.drop_table('postmaster_admins')
