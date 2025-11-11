"""add_article_analytics_table

Revision ID: bf07c7c9a81b
Revises: 6134904aa8f0
Create Date: 2025-11-11 15:35:23.812194

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'bf07c7c9a81b'
down_revision = '6134904aa8f0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create article_analytics table
    op.create_table(
        'article_analytics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('article_id', UUID(as_uuid=True), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False),
        
        # View metrics
        sa.Column('total_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('direct_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rss_views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('search_views', sa.Integer(), nullable=False, server_default='0'),
        
        # Engagement metrics
        sa.Column('avg_read_time_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_scroll_percentage', sa.DECIMAL(5, 2), nullable=False, server_default='0'),
        sa.Column('completion_rate', sa.DECIMAL(5, 4), nullable=False, server_default='0'),
        
        # Social metrics
        sa.Column('bookmark_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('share_count', sa.Integer(), nullable=False, server_default='0'),
        
        # Performance scores
        sa.Column('trending_score', sa.DECIMAL(5, 2), nullable=False, server_default='0'),
        sa.Column('performance_percentile', sa.Integer(), nullable=False, server_default='0'),
        
        # Timestamps
        sa.Column('last_calculated_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    
    # Create unique constraint
    op.create_unique_constraint('uq_article_analytics_article_id', 'article_analytics', ['article_id'])
    
    # Create indexes for performance
    op.create_index('idx_article_analytics_article_id', 'article_analytics', ['article_id'])
    op.create_index(
        'idx_article_analytics_trending_score', 
        'article_analytics', 
        ['trending_score'],
        postgresql_using='btree',
        postgresql_ops={'trending_score': 'DESC'}
    )
    op.create_index(
        'idx_article_analytics_performance', 
        'article_analytics', 
        ['performance_percentile'],
        postgresql_using='btree',
        postgresql_ops={'performance_percentile': 'DESC'}
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_article_analytics_performance', table_name='article_analytics')
    op.drop_index('idx_article_analytics_trending_score', table_name='article_analytics')
    op.drop_index('idx_article_analytics_article_id', table_name='article_analytics')
    
    # Drop unique constraint
    op.drop_constraint('uq_article_analytics_article_id', 'article_analytics', type_='unique')
    
    # Drop table
    op.drop_table('article_analytics')
