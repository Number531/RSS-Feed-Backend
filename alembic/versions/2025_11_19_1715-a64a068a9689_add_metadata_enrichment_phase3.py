"""add_metadata_enrichment_phase3

Revision ID: a64a068a9689
Revises: d8c51b626a36
Create Date: 2025-11-19 17:15:41.914416

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a64a068a9689'
down_revision = 'd8c51b626a36'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add metadata enrichment columns
    op.add_column('articles', sa.Column('timeline_event_count', sa.Integer(), nullable=True))
    op.add_column('articles', sa.Column('reference_count', sa.Integer(), nullable=True))
    op.add_column('articles', sa.Column('margin_note_count', sa.Integer(), nullable=True))
    op.add_column('articles', sa.Column('fact_check_mode', sa.String(20), nullable=True))
    op.add_column('articles', sa.Column('fact_check_processing_time', sa.Integer(), nullable=True))
    op.add_column('articles', sa.Column('synthesis_generated_at', sa.TIMESTAMP(timezone=True), nullable=True))
    
    # Populate metadata columns for existing synthesis articles
    op.execute("""
        UPDATE articles
        SET 
            timeline_event_count = CASE 
                WHEN jsonb_typeof(article_data->'event_timeline') = 'array' 
                THEN jsonb_array_length(article_data->'event_timeline')
                ELSE 0
            END,
            reference_count = CASE 
                WHEN jsonb_typeof(article_data->'references') = 'array' 
                THEN jsonb_array_length(article_data->'references')
                ELSE 0
            END,
            margin_note_count = CASE 
                WHEN jsonb_typeof(article_data->'margin_notes') = 'array' 
                THEN jsonb_array_length(article_data->'margin_notes')
                ELSE 0
            END,
            fact_check_mode = CASE 
                WHEN synthesis_article IS NOT NULL THEN 'synthesis'
                WHEN fact_check_verdict IS NOT NULL THEN 'standard'
                ELSE NULL
            END,
            fact_check_processing_time = (article_data->'generation_metadata'->>'processing_time_seconds')::integer,
            synthesis_generated_at = (article_data->'generation_metadata'->>'generated_at')::timestamp with time zone
        WHERE synthesis_article IS NOT NULL OR fact_check_verdict IS NOT NULL
    """)
    
    # Create trigger to auto-set synthesis_generated_at on insert/update
    op.execute("""
        CREATE OR REPLACE FUNCTION update_synthesis_generated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.synthesis_article IS NOT NULL AND OLD.synthesis_article IS NULL THEN
                NEW.synthesis_generated_at = NOW();
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trigger_update_synthesis_generated_at
        BEFORE INSERT OR UPDATE ON articles
        FOR EACH ROW
        EXECUTE FUNCTION update_synthesis_generated_at();
    """)
    
    # Create indexes for filtering
    op.create_index('idx_articles_fact_check_mode', 'articles', ['fact_check_mode'])
    op.create_index('idx_articles_synthesis_generated_at', 'articles', ['synthesis_generated_at'])


def downgrade() -> None:
    # Drop trigger and function
    op.execute('DROP TRIGGER IF EXISTS trigger_update_synthesis_generated_at ON articles')
    op.execute('DROP FUNCTION IF EXISTS update_synthesis_generated_at()')
    
    # Drop indexes
    op.drop_index('idx_articles_synthesis_generated_at', table_name='articles')
    op.drop_index('idx_articles_fact_check_mode', table_name='articles')
    
    # Drop columns
    op.drop_column('articles', 'synthesis_generated_at')
    op.drop_column('articles', 'fact_check_processing_time')
    op.drop_column('articles', 'fact_check_mode')
    op.drop_column('articles', 'margin_note_count')
    op.drop_column('articles', 'reference_count')
    op.drop_column('articles', 'timeline_event_count')
