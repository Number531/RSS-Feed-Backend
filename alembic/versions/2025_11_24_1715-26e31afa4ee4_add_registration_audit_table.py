"""Add registration audit table

Revision ID: 26e31afa4ee4
Revises: 2317b7aeeb89
Create Date: 2025-11-24 17:15:50.069264

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26e31afa4ee4'
down_revision = '2317b7aeeb89'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create registration_audit table
    op.create_table(
        'registration_audit',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('failure_reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('registration_audit_user_id_fkey'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('registration_audit_pkey'))
    )
    
    # Create indexes
    op.create_index(op.f('ix_registration_audit_email'), 'registration_audit', ['email'], unique=False)
    op.create_index(op.f('ix_registration_audit_username'), 'registration_audit', ['username'], unique=False)
    op.create_index(op.f('ix_registration_audit_success'), 'registration_audit', ['success'], unique=False)
    op.create_index(op.f('ix_registration_audit_created_at'), 'registration_audit', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_registration_audit_created_at'), table_name='registration_audit')
    op.drop_index(op.f('ix_registration_audit_success'), table_name='registration_audit')
    op.drop_index(op.f('ix_registration_audit_username'), table_name='registration_audit')
    op.drop_index(op.f('ix_registration_audit_email'), table_name='registration_audit')
    
    # Drop table
    op.drop_table('registration_audit')
