"""Add user feed subscriptions table

Revision ID: 005
Revises: 004
Create Date: 2025-10-14 15:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_feed_subscriptions table
    op.create_table(
        'user_feed_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('feed_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('subscribed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['feed_id'], ['rss_sources.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'feed_id', name='unique_user_feed_subscription')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_user_feed_subscriptions_user_id', 'user_feed_subscriptions', ['user_id'])
    op.create_index('ix_user_feed_subscriptions_feed_id', 'user_feed_subscriptions', ['feed_id'])
    op.create_index('ix_user_feed_subscriptions_is_active', 'user_feed_subscriptions', ['is_active'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_user_feed_subscriptions_is_active', table_name='user_feed_subscriptions')
    op.drop_index('ix_user_feed_subscriptions_feed_id', table_name='user_feed_subscriptions')
    op.drop_index('ix_user_feed_subscriptions_user_id', table_name='user_feed_subscriptions')
    
    # Drop table
    op.drop_table('user_feed_subscriptions')
