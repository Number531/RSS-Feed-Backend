"""enhance_fact_check_source_storage

Revision ID: d257e5cdae04
Revises: 4bbd09c7c9af
Create Date: 2025-11-04 12:06:28.629009

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd257e5cdae04'
down_revision = '4bbd09c7c9af'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # HIGH PRIORITY #1: Add source_breakdown JSONB column
    op.add_column(
        'article_fact_checks',
        sa.Column('source_breakdown', sa.dialects.postgresql.JSONB(), nullable=True, server_default='{}')
    )
    
    # Create GIN index for source_breakdown for fast JSONB queries
    op.create_index(
        'idx_article_fact_checks_source_breakdown',
        'article_fact_checks',
        ['source_breakdown'],
        unique=False,
        postgresql_using='gin'
    )
    
    # HIGH PRIORITY #2: Increase source_consensus column size
    op.alter_column(
        'article_fact_checks',
        'source_consensus',
        type_=sa.String(50),
        existing_type=sa.String(20),
        existing_nullable=True
    )
    
    # MEDIUM PRIORITY #3: Add composite indexes for common analytics queries
    # Verdict + date for time-series verdict analysis
    op.create_index(
        'idx_article_fact_checks_verdict_date',
        'article_fact_checks',
        ['verdict', sa.text('fact_checked_at DESC')],
        unique=False
    )
    
    # Score + date for credibility trending
    op.create_index(
        'idx_article_fact_checks_score_date',
        'article_fact_checks',
        [sa.text('credibility_score DESC'), sa.text('fact_checked_at DESC')],
        unique=False
    )
    
    # MEDIUM PRIORITY #4: Add partial index on num_sources (only non-zero)
    op.execute(
        "CREATE INDEX idx_article_fact_checks_num_sources "
        "ON article_fact_checks(num_sources) "
        "WHERE num_sources > 0"
    )
    
    # LOW PRIORITY #5: Add materialized summary fields for source analysis
    op.add_column(
        'article_fact_checks',
        sa.Column('primary_source_type', sa.String(20), nullable=True)
    )
    
    op.add_column(
        'article_fact_checks',
        sa.Column('source_diversity_score', sa.Numeric(3, 2), nullable=True)
    )
    
    # Create index on primary_source_type for fast filtering
    op.create_index(
        'idx_article_fact_checks_primary_source',
        'article_fact_checks',
        ['primary_source_type'],
        unique=False
    )


def downgrade() -> None:
    # Remove indexes first
    op.drop_index('idx_article_fact_checks_primary_source', table_name='article_fact_checks')
    op.drop_index('idx_article_fact_checks_num_sources', table_name='article_fact_checks')
    op.drop_index('idx_article_fact_checks_score_date', table_name='article_fact_checks')
    op.drop_index('idx_article_fact_checks_verdict_date', table_name='article_fact_checks')
    op.drop_index('idx_article_fact_checks_source_breakdown', table_name='article_fact_checks')
    
    # Remove columns
    op.drop_column('article_fact_checks', 'source_diversity_score')
    op.drop_column('article_fact_checks', 'primary_source_type')
    op.drop_column('article_fact_checks', 'source_breakdown')
    
    # Revert source_consensus size
    op.alter_column(
        'article_fact_checks',
        'source_consensus',
        type_=sa.String(20),
        existing_type=sa.String(50),
        existing_nullable=True
    )
