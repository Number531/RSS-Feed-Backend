"""add_ux_enhancements_phase4

Revision ID: 2317b7aeeb89
Revises: a64a068a9689
Create Date: 2025-11-19 17:16:07.310529

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2317b7aeeb89'
down_revision = 'a64a068a9689'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add UX enhancement columns
    op.add_column('articles', sa.Column('synthesis_read_minutes', sa.Integer(), nullable=True))
    op.add_column('articles', sa.Column('verdict_color', sa.String(20), nullable=True))
    
    # Populate UX columns for existing synthesis articles
    op.execute("""
        UPDATE articles
        SET 
            synthesis_read_minutes = CASE 
                WHEN synthesis_word_count IS NOT NULL 
                THEN CEIL(synthesis_word_count / 200.0)::integer
                ELSE NULL
            END,
            verdict_color = CASE 
                WHEN fact_check_verdict = 'TRUE' THEN 'green'
                WHEN fact_check_verdict = 'MOSTLY TRUE' THEN 'lime'
                WHEN fact_check_verdict = 'MIXED' THEN 'yellow'
                WHEN fact_check_verdict = 'MOSTLY FALSE' THEN 'orange'
                WHEN fact_check_verdict = 'FALSE' THEN 'red'
                WHEN fact_check_verdict LIKE 'UNVERIFIED%' THEN 'gray'
                ELSE NULL
            END
        WHERE synthesis_article IS NOT NULL
    """)
    
    # Create index for verdict filtering
    op.create_index('idx_articles_verdict_color', 'articles', ['verdict_color'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_articles_verdict_color', table_name='articles')
    
    # Drop columns
    op.drop_column('articles', 'verdict_color')
    op.drop_column('articles', 'synthesis_read_minutes')
