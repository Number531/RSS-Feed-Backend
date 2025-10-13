"""add bookmarks table

Revision ID: 001
Revises: 
Create Date: 2025-10-10 19:15:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create bookmarks table with indexes and constraints."""
    # Create bookmarks table
    op.create_table(
        'bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('collection', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'article_id', name='uq_user_article_bookmark'),
    )
    
    # Create indexes for performance
    op.create_index('idx_bookmarks_user_id', 'bookmarks', ['user_id'])
    op.create_index('idx_bookmarks_article_id', 'bookmarks', ['article_id'])
    op.create_index('idx_bookmarks_created_at', 'bookmarks', ['created_at'])
    op.create_index(
        'idx_bookmarks_collection',
        'bookmarks',
        ['collection'],
        postgresql_where=sa.text('collection IS NOT NULL')
    )


def downgrade() -> None:
    """Drop bookmarks table and all indexes."""
    op.drop_index('idx_bookmarks_collection', table_name='bookmarks')
    op.drop_index('idx_bookmarks_created_at', table_name='bookmarks')
    op.drop_index('idx_bookmarks_article_id', table_name='bookmarks')
    op.drop_index('idx_bookmarks_user_id', table_name='bookmarks')
    op.drop_table('bookmarks')
