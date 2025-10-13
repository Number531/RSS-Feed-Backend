"""Add notifications system

Revision ID: 004
Revises: 003
Create Date: 2025-10-11 21:09:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create notifications and user_notification_preferences tables."""
    
    # Create user_notification_preferences table
    op.create_table(
        'user_notification_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('vote_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('reply_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('mention_notifications', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_notifications', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create index on user_id for preferences
    op.create_index('ix_user_notification_preferences_user_id', 'user_notification_preferences', ['user_id'])
    
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_entity_type', sa.String(50), nullable=True),
        sa.Column('related_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes for notifications
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_type', 'notifications', ['type'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_actor_id', 'notifications', ['actor_id'])
    
    # Composite index for common queries (user_id + is_read + created_at)
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read', 'created_at'])


def downgrade() -> None:
    """Drop notifications and user_notification_preferences tables."""
    
    # Drop notifications table and its indexes
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_index('ix_notifications_actor_id', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_index('ix_notifications_type', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_table('notifications')
    
    # Drop user_notification_preferences table and its indexes
    op.drop_index('ix_user_notification_preferences_user_id', table_name='user_notification_preferences')
    op.drop_table('user_notification_preferences')
