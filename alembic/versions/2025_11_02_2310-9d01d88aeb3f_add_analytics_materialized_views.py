"""add_analytics_materialized_views

Revision ID: 9d01d88aeb3f
Revises: 458601019622
Create Date: 2025-11-02 23:10:30.798089

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d01d88aeb3f'
down_revision = '458601019622'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create daily analytics summary materialized view
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_daily_summary AS
        SELECT 
            DATE(a.created_at) as summary_date,
            COUNT(DISTINCT a.id) as articles_count,
            COUNT(DISTINCT a.rss_source_id) as sources_count,
            AVG(afc.credibility_score) as avg_credibility,
            AVG(afc.confidence) as avg_confidence,
            COUNT(CASE WHEN afc.verdict = 'TRUE' THEN 1 END) as true_count,
            COUNT(CASE WHEN afc.verdict = 'FALSE' THEN 1 END) as false_count,
            COUNT(CASE WHEN afc.verdict = 'MISLEADING' THEN 1 END) as misleading_count,
            SUM(afc.claims_analyzed) as total_claims
        FROM articles a
        JOIN article_fact_checks afc ON a.id = afc.article_id
        WHERE a.created_at >= CURRENT_DATE - INTERVAL '365 days'
        GROUP BY DATE(a.created_at)
    """)
    
    # Create unique index on daily summary
    op.execute("""
        CREATE UNIQUE INDEX idx_analytics_daily_summary_date 
        ON analytics_daily_summary (summary_date DESC)
    """)
    
    # Create source reliability materialized view
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_source_reliability AS
        SELECT 
            rs.id as source_id,
            rs.name as source_name,
            rs.category,
            COUNT(DISTINCT a.id) as articles_count,
            AVG(afc.credibility_score) as avg_credibility,
            AVG(afc.confidence) as avg_confidence,
            COUNT(CASE WHEN afc.verdict = 'TRUE' THEN 1 END) as true_verdicts,
            COUNT(CASE WHEN afc.verdict = 'FALSE' THEN 1 END) as false_verdicts,
            COUNT(CASE WHEN afc.verdict = 'MISLEADING' THEN 1 END) as misleading_verdicts,
            SUM(afc.claims_analyzed) as total_claims,
            MAX(a.created_at) as last_article_date
        FROM rss_sources rs
        JOIN articles a ON rs.id = a.rss_source_id
        JOIN article_fact_checks afc ON a.id = afc.article_id
        WHERE a.created_at >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY rs.id, rs.name, rs.category
        HAVING COUNT(DISTINCT a.id) >= 5
    """)
    
    # Create indexes on source reliability view
    op.execute("""
        CREATE UNIQUE INDEX idx_analytics_source_reliability_id 
        ON analytics_source_reliability (source_id)
    """)
    
    op.execute("""
        CREATE INDEX idx_analytics_source_reliability_credibility 
        ON analytics_source_reliability (avg_credibility DESC)
    """)
    
    # Create category analytics materialized view
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_category_summary AS
        SELECT 
            a.category,
            COUNT(DISTINCT a.id) as articles_count,
            AVG(afc.credibility_score) as avg_credibility,
            COUNT(CASE WHEN afc.verdict IN ('FALSE', 'MISLEADING') THEN 1 END) as risk_count,
            COUNT(CASE WHEN afc.verdict IN ('FALSE', 'MISLEADING') THEN 1 END)::FLOAT 
                / NULLIF(COUNT(a.id), 0) * 100 as false_rate,
            ARRAY(
                SELECT DISTINCT name 
                FROM unnest(ARRAY_AGG(DISTINCT rs.name)) AS name 
                ORDER BY name 
                LIMIT 5
            ) as top_sources
        FROM articles a
        JOIN article_fact_checks afc ON a.id = afc.article_id
        JOIN rss_sources rs ON a.rss_source_id = rs.id
        WHERE a.created_at >= CURRENT_DATE - INTERVAL '90 days'
          AND a.category IS NOT NULL
        GROUP BY a.category
        HAVING COUNT(DISTINCT a.id) >= 5
    """)
    
    # Create index on category summary
    op.execute("""
        CREATE UNIQUE INDEX idx_analytics_category_summary_category 
        ON analytics_category_summary (category)
    """)


def downgrade() -> None:
    # Drop materialized views (indexes will be automatically dropped)
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics_category_summary")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics_source_reliability")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS analytics_daily_summary")
