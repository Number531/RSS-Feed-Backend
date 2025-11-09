"""add_crawled_content_to_articles

Revision ID: 86f26af133fb
Revises: 271d7bbeaeda
Create Date: 2025-11-08 22:34:03.033077

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86f26af133fb'
down_revision = '271d7bbeaeda'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add crawled_content column to articles table
    op.add_column(
        'articles',
        sa.Column('crawled_content', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    # Remove crawled_content column from articles table
    op.drop_column('articles', 'crawled_content')
