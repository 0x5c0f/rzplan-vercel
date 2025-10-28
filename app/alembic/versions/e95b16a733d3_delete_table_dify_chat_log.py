"""delete table dify chat log

Revision ID: e95b16a733d3
Revises: 082be190a666
Create Date: 2025-10-28 16:47:07.926514

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e95b16a733d3'
down_revision = '082be190a666'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the dify_chat_log table
    op.drop_table('dify_chat_log')


def downgrade():
    # Create the dify_chat_log table
    op.create_table(
        'dify_chat_log',
        sa.Column('id', sa.UUID(), nullable=False),  # UUID as primary key
        sa.Column('dify_user_id', sa.String(length=50), nullable=False),
        sa.Column('dify_app_id', sa.String(length=50), nullable=False),
        sa.Column('user_name', sa.String(length=50), nullable=True),
        sa.Column('user_contact', sa.String(length=50), nullable=True),
        sa.Column('ask', sa.Text(), nullable=True), 
        sa.Column('answer', sa.Text(), nullable=True), 
        sa.Column('created_at', sa.DateTime(), nullable=True)  # Timestamp of creation
    )