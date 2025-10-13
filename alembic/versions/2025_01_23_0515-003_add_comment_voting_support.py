"""add comment voting support

Revision ID: 003
Revises: 002
Create Date: 2025-01-23 05:15:00

This migration adds support for voting on comments:
1. Makes article_id nullable in votes table
2. Adds comment_id column to votes table
3. Adds check constraint to ensure vote targets either article OR comment
4. Adds vote_count column to comments table
5. Creates necessary indexes for performance
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add comment voting support."""
    
    # Step 1: Make article_id nullable in votes table
    op.alter_column(
        'votes',
        'article_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )
    
    # Step 2: Add comment_id column to votes table
    op.add_column(
        'votes',
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Step 3: Add foreign key constraint for comment_id
    op.create_foreign_key(
        'fk_votes_comment_id_comments',
        'votes',
        'comments',
        ['comment_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Step 4: Create index on comment_id for performance
    op.create_index(
        'ix_votes_comment_id',
        'votes',
        ['comment_id']
    )
    
    # Step 5: Add check constraint to ensure vote targets either article OR comment
    op.create_check_constraint(
        'vote_target_check',
        'votes',
        '(article_id IS NOT NULL AND comment_id IS NULL) OR (article_id IS NULL AND comment_id IS NOT NULL)'
    )
    
    # Step 6: Add unique constraint for comment votes (user can only vote once per comment)
    op.create_unique_constraint(
        'unique_user_comment_vote',
        'votes',
        ['user_id', 'comment_id']
    )
    
    # Step 7: Add vote_count column to comments table
    op.add_column(
        'comments',
        sa.Column('vote_count', sa.Integer(), nullable=False, server_default='0')
    )
    
    # Step 8: Create index on vote_count for sorting/filtering
    op.create_index(
        'ix_comments_vote_count',
        'comments',
        ['vote_count'],
        unique=False
    )


def downgrade() -> None:
    """Remove comment voting support."""
    
    # Drop indexes
    op.drop_index('ix_comments_vote_count', table_name='comments')
    op.drop_index('ix_votes_comment_id', table_name='votes')
    
    # Drop constraints
    op.drop_constraint('unique_user_comment_vote', 'votes', type_='unique')
    op.drop_constraint('vote_target_check', 'votes', type_='check')
    op.drop_constraint('fk_votes_comment_id_comments', 'votes', type_='foreignkey')
    
    # Drop columns
    op.drop_column('comments', 'vote_count')
    op.drop_column('votes', 'comment_id')
    
    # Make article_id non-nullable again
    op.alter_column(
        'votes',
        'article_id',
        existing_type=postgresql.UUID(),
        nullable=False
    )
