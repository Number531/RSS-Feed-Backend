"""add thread subscriptions table

Revision ID: 4d69fb0734b3
Revises: 730687afff1c
Create Date: 2025-11-11 16:56:55.702199

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4d69fb0734b3'
down_revision = '730687afff1c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'thread_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('subscribed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'comment_id', name='uq_user_comment_subscription'),
    )


def downgrade() -> None:
    op.drop_table('thread_subscriptions')
