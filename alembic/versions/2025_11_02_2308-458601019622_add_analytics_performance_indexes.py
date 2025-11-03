"""add_analytics_performance_indexes

Revision ID: 458601019622
Revises: 006
Create Date: 2025-11-02 23:08:27.730188

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '458601019622'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Articles table indexes for analytics performance
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_articles_created_at "
        "ON articles (created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_articles_source_created "
        "ON articles (rss_source_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_articles_category_created "
        "ON articles (category, created_at DESC)"
    )
    
    # Article fact checks indexes for analytics queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_article_fact_checks_article_id "
        "ON article_fact_checks (article_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_article_fact_checks_verdict "
        "ON article_fact_checks (verdict, credibility_score)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_article_fact_checks_confidence "
        "ON article_fact_checks (confidence)"
    )


def downgrade() -> None:
    # Drop analytics indexes
    op.execute("DROP INDEX IF EXISTS idx_articles_created_at")
    op.execute("DROP INDEX IF EXISTS idx_articles_source_created")
    op.execute("DROP INDEX IF EXISTS idx_articles_category_created")
    op.execute("DROP INDEX IF EXISTS idx_article_fact_checks_article_id")
    op.execute("DROP INDEX IF EXISTS idx_article_fact_checks_verdict")
    op.execute("DROP INDEX IF EXISTS idx_article_fact_checks_confidence")
