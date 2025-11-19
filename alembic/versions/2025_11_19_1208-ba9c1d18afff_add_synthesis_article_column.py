"""add synthesis article column

Revision ID: ba9c1d18afff
Revises: 830e6ab26ebe
Create Date: 2025-11-19 12:08:34.950135

This migration adds support for storing full synthesis mode articles.
Synthesis mode generates 1,400-2,500 word journalistic articles with
embedded citations, context analysis, and narrative prose.

Zero-downtime migration: adds nullable column with partial index.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ba9c1d18afff'
down_revision = '830e6ab26ebe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add synthesis_article column for full markdown articles."""
    
    # 1. Add nullable TEXT column for synthesis articles
    # This is zero-downtime because it's nullable and has no default
    op.add_column(
        'articles',
        sa.Column('synthesis_article', sa.Text(), nullable=True)
    )
    
    # 2. Add comment to column for documentation
    op.execute("""
        COMMENT ON COLUMN articles.synthesis_article IS 
        'Full markdown article from synthesis fact-check mode (1,400-2,500 words). 
         Contains narrative prose with embedded citations, context analysis, and 
         event timeline. Only populated when validation_mode=synthesis.';
    """)
    
    # 3. Create partial index (only indexes non-null values)
    # This saves space and improves query performance
    op.create_index(
        'ix_articles_has_synthesis',
        'articles',
        ['id'],
        unique=False,
        postgresql_where=sa.text('synthesis_article IS NOT NULL')
    )
    
    # 4. Create GIN index for full-text search on synthesis articles
    # This enables fast text search within synthesis articles
    op.execute("""
        CREATE INDEX ix_articles_synthesis_fts 
        ON articles 
        USING gin(to_tsvector('english', COALESCE(synthesis_article, '')))
        WHERE synthesis_article IS NOT NULL;
    """)
    
    # 5. Add index on fact-checked articles with synthesis mode
    # Helps query performance for "give me all synthesis articles"
    op.execute("""
        CREATE INDEX ix_articles_synthesis_fact_checked 
        ON articles (fact_checked_at DESC, id)
        WHERE synthesis_article IS NOT NULL;
    """)


def downgrade() -> None:
    """Remove synthesis_article column and related indexes."""
    
    # Drop indexes first (required before dropping column)
    op.drop_index('ix_articles_synthesis_fact_checked', table_name='articles')
    op.drop_index('ix_articles_synthesis_fts', table_name='articles')
    op.drop_index('ix_articles_has_synthesis', table_name='articles')
    
    # Drop column
    op.drop_column('articles', 'synthesis_article')
