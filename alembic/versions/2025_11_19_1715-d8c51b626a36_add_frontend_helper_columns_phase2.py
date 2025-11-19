"""add_frontend_helper_columns_phase2

Revision ID: d8c51b626a36
Revises: ba9c1d18afff
Create Date: 2025-11-19 17:15:17.028176

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8c51b626a36'
down_revision = 'ba9c1d18afff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram text search
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    
    # Add computed helper columns for frontend optimization
    op.add_column('articles', sa.Column('has_synthesis', sa.Boolean(), nullable=True))
    op.add_column('articles', sa.Column('synthesis_preview', sa.Text(), nullable=True))
    op.add_column('articles', sa.Column('synthesis_word_count', sa.Integer(), nullable=True))
    op.add_column('articles', sa.Column('has_context_emphasis', sa.Boolean(), nullable=True))
    op.add_column('articles', sa.Column('has_timeline', sa.Boolean(), nullable=True))
    
    # Populate computed columns for existing synthesis articles
    op.execute("""
        UPDATE articles
        SET 
            has_synthesis = (synthesis_article IS NOT NULL),
            synthesis_preview = LEFT(synthesis_article, 500),
            synthesis_word_count = array_length(regexp_split_to_array(synthesis_article, '\\s+'), 1),
            has_context_emphasis = (article_data->>'context_and_emphasis' IS NOT NULL),
            has_timeline = (article_data->>'event_timeline' IS NOT NULL)
        WHERE synthesis_article IS NOT NULL
    """)
    
    # Create indexes for efficient filtering
    op.create_index('idx_articles_has_synthesis_v2', 'articles', ['has_synthesis'])
    op.create_index('idx_articles_synthesis_ready', 'articles', ['has_synthesis', 'synthesis_word_count'])
    op.create_index('idx_articles_synthesis_preview_fts', 'articles', ['synthesis_preview'], 
                    postgresql_using='gin', 
                    postgresql_ops={'synthesis_preview': 'gin_trgm_ops'})


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_articles_synthesis_preview_fts', table_name='articles')
    op.drop_index('idx_articles_synthesis_ready', table_name='articles')
    op.drop_index('idx_articles_has_synthesis_v2', table_name='articles')
    
    # Drop columns
    op.drop_column('articles', 'has_timeline')
    op.drop_column('articles', 'has_context_emphasis')
    op.drop_column('articles', 'synthesis_word_count')
    op.drop_column('articles', 'synthesis_preview')
    op.drop_column('articles', 'has_synthesis')
