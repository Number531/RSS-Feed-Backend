"""add comment mentions table

Revision ID: 730687afff1c
Revises: bf07c7c9a81b
Create Date: 2025-11-11 16:16:19.999749

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '730687afff1c'
down_revision = 'bf07c7c9a81b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'comment_mentions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('mentioned_user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('mentioned_by_user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mentioned_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mentioned_by_user_id'], ['users.id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('comment_mentions')
