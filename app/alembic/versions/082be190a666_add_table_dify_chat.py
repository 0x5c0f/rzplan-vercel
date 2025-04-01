"""add table dify_chat_log

Revision ID: 082be190a666
Revises: 2e9baf336715
Create Date: 2025-04-01 15:43:18.187864

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '082be190a666'
down_revision = '2e9baf336715'
branch_labels = None
depends_on = None


def upgrade():
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


def downgrade():
    # Drop the dify_chat_log table
    op.drop_table('dify_chat_log')
