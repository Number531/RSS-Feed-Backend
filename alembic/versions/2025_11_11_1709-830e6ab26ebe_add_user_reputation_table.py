"""add user reputation table

Revision ID: 830e6ab26ebe
Revises: 4d69fb0734b3
Create Date: 2025-11-11 17:09:52.913393
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '830e6ab26ebe'
down_revision = '4d69fb0734b3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_reputation',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('reputation_score', sa.Integer(), nullable=False, default=0, index=True),
        sa.Column('total_votes_received', sa.Integer(), nullable=False, default=0),
        sa.Column('total_comments', sa.Integer(), nullable=False, default=0),
        sa.Column('total_articles_bookmarked', sa.Integer(), nullable=False, default=0),
        sa.Column('helpful_votes', sa.Integer(), nullable=False, default=0),
        sa.Column('rank', sa.Integer(), nullable=True, index=True),
        sa.Column('percentile', sa.Integer(), nullable=True),
        sa.Column('badges', postgresql.JSONB(), nullable=True),
        sa.Column('last_calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('user_reputation')
    pass
