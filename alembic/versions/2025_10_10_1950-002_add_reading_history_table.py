"""add reading history table

Revision ID: 002
Revises: 001
Create Date: 2025-10-10 19:50:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create reading_history table with indexes."""
    # Create reading_history table
    op.create_table(
        'reading_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('viewed_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        sa.Column('scroll_percentage', sa.DECIMAL(5, 2), nullable=True),
    )
    
    # Create indexes for performance
    op.create_index('idx_reading_history_user_id', 'reading_history', ['user_id'])
    op.create_index('idx_reading_history_article_id', 'reading_history', ['article_id'])
    op.create_index('idx_reading_history_viewed_at', 'reading_history', ['viewed_at'])
    op.create_index('idx_reading_history_user_viewed', 'reading_history', ['user_id', 'viewed_at'])


def downgrade() -> None:
    """Drop reading_history table and all indexes."""
    op.drop_index('idx_reading_history_user_viewed', table_name='reading_history')
    op.drop_index('idx_reading_history_viewed_at', table_name='reading_history')
    op.drop_index('idx_reading_history_article_id', table_name='reading_history')
    op.drop_index('idx_reading_history_user_id', table_name='reading_history')
    op.drop_table('reading_history')
