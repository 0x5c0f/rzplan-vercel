"""merge branch heads

Revision ID: 3223deb356ca
Revises: 2e9baf336715, fe56fa70289e
Create Date: 2026-01-28 10:48:29.592207

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '3223deb356ca'
down_revision = ('2e9baf336715', 'fe56fa70289e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
