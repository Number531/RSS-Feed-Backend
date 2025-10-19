"""Add fact-check system tables and columns

Revision ID: 006
Revises: 005
Create Date: 2025-10-17 22:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add fact-check cache columns to articles table
    op.add_column('articles', sa.Column('fact_check_score', sa.Integer(), nullable=True))
    op.add_column('articles', sa.Column('fact_check_verdict', sa.String(50), nullable=True))
    op.add_column('articles', sa.Column('fact_checked_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create indexes for filtering/sorting by fact-check status
    op.create_index('ix_articles_fact_check_score', 'articles', ['fact_check_score'])
    op.create_index('ix_articles_fact_check_verdict', 'articles', ['fact_check_verdict'])
    op.create_index('ix_articles_fact_checked_at', 'articles', ['fact_checked_at'])
    
    # Step 2: Create article_fact_checks table for detailed fact-check results
    op.create_table(
        'article_fact_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        
        # Core fact-check results
        sa.Column('verdict', sa.String(50), nullable=False),
        sa.Column('credibility_score', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        
        # Claim statistics
        sa.Column('claims_analyzed', sa.Integer(), nullable=True),
        sa.Column('claims_validated', sa.Integer(), nullable=True),
        sa.Column('claims_true', sa.Integer(), nullable=True),
        sa.Column('claims_false', sa.Integer(), nullable=True),
        sa.Column('claims_misleading', sa.Integer(), nullable=True),
        sa.Column('claims_unverified', sa.Integer(), nullable=True),
        
        # Full validation data (JSONB for flexibility)
        sa.Column('validation_results', postgresql.JSONB(), nullable=False),
        
        # Evidence quality metrics
        sa.Column('num_sources', sa.Integer(), nullable=True),
        sa.Column('source_consensus', sa.String(20), nullable=True),
        
        # Processing metadata
        sa.Column('job_id', sa.String(255), nullable=False, unique=True),
        sa.Column('validation_mode', sa.String(20), nullable=True),
        sa.Column('processing_time_seconds', sa.Integer(), nullable=True),
        sa.Column('api_costs', postgresql.JSONB(), nullable=True),
        
        # Timestamps
        sa.Column('fact_checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraint
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for fact_checks table
    op.create_index('ix_article_fact_checks_article_id', 'article_fact_checks', ['article_id'])
    op.create_index('ix_article_fact_checks_verdict', 'article_fact_checks', ['verdict'])
    op.create_index('ix_article_fact_checks_credibility_score', 'article_fact_checks', ['credibility_score'])
    op.create_index('ix_article_fact_checks_job_id', 'article_fact_checks', ['job_id'])
    op.create_index('ix_article_fact_checks_fact_checked_at', 'article_fact_checks', ['fact_checked_at'])
    
    # JSONB GIN index for searching within validation_results (using raw SQL)
    op.execute(
        "CREATE INDEX ix_article_fact_checks_validation_results_gin "
        "ON article_fact_checks USING gin (validation_results)"
    )
    
    # Step 3: Create source_credibility_scores table for news outlet tracking
    op.create_table(
        'source_credibility_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('rss_source_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Aggregated credibility metrics
        sa.Column('average_score', sa.DECIMAL(5, 2), nullable=False),
        sa.Column('total_articles_checked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('true_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('false_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('misleading_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unverified_count', sa.Integer(), nullable=False, server_default='0'),
        
        # Time period for scoring
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),  # 'daily', 'weekly', 'monthly', 'all_time'
        
        # Trend analysis (JSONB for historical data points)
        sa.Column('trend_data', postgresql.JSONB(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Foreign key constraint
        sa.ForeignKeyConstraint(['rss_source_id'], ['rss_sources.id'], ondelete='CASCADE'),
        
        # Unique constraint for source + period type combination
        sa.UniqueConstraint('rss_source_id', 'period_type', 'period_start', name='unique_source_period_score')
    )
    
    # Create indexes for credibility_scores table
    op.create_index('ix_source_credibility_scores_rss_source_id', 'source_credibility_scores', ['rss_source_id'])
    op.create_index('ix_source_credibility_scores_period_type', 'source_credibility_scores', ['period_type'])
    op.create_index('ix_source_credibility_scores_average_score', 'source_credibility_scores', ['average_score'])
    op.create_index('ix_source_credibility_scores_period_end', 'source_credibility_scores', ['period_end'])


def downgrade() -> None:
    # Drop source_credibility_scores table
    op.drop_index('ix_source_credibility_scores_period_end', table_name='source_credibility_scores')
    op.drop_index('ix_source_credibility_scores_average_score', table_name='source_credibility_scores')
    op.drop_index('ix_source_credibility_scores_period_type', table_name='source_credibility_scores')
    op.drop_index('ix_source_credibility_scores_rss_source_id', table_name='source_credibility_scores')
    op.drop_table('source_credibility_scores')
    
    # Drop article_fact_checks table
    op.execute('DROP INDEX IF EXISTS ix_article_fact_checks_validation_results_gin')
    op.drop_index('ix_article_fact_checks_fact_checked_at', table_name='article_fact_checks')
    op.drop_index('ix_article_fact_checks_job_id', table_name='article_fact_checks')
    op.drop_index('ix_article_fact_checks_credibility_score', table_name='article_fact_checks')
    op.drop_index('ix_article_fact_checks_verdict', table_name='article_fact_checks')
    op.drop_index('ix_article_fact_checks_article_id', table_name='article_fact_checks')
    op.drop_table('article_fact_checks')
    
    # Drop articles table columns and indexes
    op.drop_index('ix_articles_fact_checked_at', table_name='articles')
    op.drop_index('ix_articles_fact_check_verdict', table_name='articles')
    op.drop_index('ix_articles_fact_check_score', table_name='articles')
    op.drop_column('articles', 'fact_checked_at')
    op.drop_column('articles', 'fact_check_verdict')
    op.drop_column('articles', 'fact_check_score')
