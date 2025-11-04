"""add_high_risk_claims_tracking

Revision ID: 271d7bbeaeda
Revises: d257e5cdae04
Create Date: 2025-11-04 12:21:47.864296

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '271d7bbeaeda'
down_revision = 'd257e5cdae04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add high_risk_claims_count column for fast risk-based queries
    op.add_column(
        'article_fact_checks',
        sa.Column('high_risk_claims_count', sa.Integer(), nullable=False, server_default='0')
    )
    
    # Add partial index for articles with high-risk claims (most common query)
    op.execute(
        "CREATE INDEX idx_article_fact_checks_high_risk "
        "ON article_fact_checks(high_risk_claims_count) "
        "WHERE high_risk_claims_count > 0"
    )
    
    # Add index for sorting by risk level
    op.create_index(
        'idx_article_fact_checks_risk_desc',
        'article_fact_checks',
        [sa.text('high_risk_claims_count DESC')],
        unique=False
    )


def downgrade() -> None:
    # Remove indexes first
    op.drop_index('idx_article_fact_checks_risk_desc', table_name='article_fact_checks')
    op.drop_index('idx_article_fact_checks_high_risk', table_name='article_fact_checks')
    
    # Remove column
    op.drop_column('article_fact_checks', 'high_risk_claims_count')
