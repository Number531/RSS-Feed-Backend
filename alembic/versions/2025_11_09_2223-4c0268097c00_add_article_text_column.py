"""add_article_text_column

Revision ID: 4c0268097c00
Revises: 86f26af133fb
Create Date: 2025-11-09 22:23:12.447590

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c0268097c00'
down_revision = '86f26af133fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add article_text column to store clean Railway-generated article content
    op.add_column(
        'articles',
        sa.Column('article_text', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('articles', 'article_text')
