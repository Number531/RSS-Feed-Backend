"""replace_article_text_with_article_data

Revision ID: 6134904aa8f0
Revises: 4c0268097c00
Create Date: 2025-11-09 23:46:19.198357

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '6134904aa8f0'
down_revision = '4c0268097c00'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop article_text column (plain text)
    op.drop_column('articles', 'article_text')
    
    # Add article_data column (structured JSON from Railway API)
    op.add_column(
        'articles',
        sa.Column('article_data', JSONB, nullable=True)
    )


def downgrade() -> None:
    # Reverse: drop article_data and restore article_text
    op.drop_column('articles', 'article_data')
    op.add_column(
        'articles',
        sa.Column('article_text', sa.Text(), nullable=True)
    )
