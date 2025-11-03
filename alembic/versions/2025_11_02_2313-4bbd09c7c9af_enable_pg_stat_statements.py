"""enable_pg_stat_statements

Revision ID: 4bbd09c7c9af
Revises: 9d01d88aeb3f
Create Date: 2025-11-02 23:13:07.093720

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4bbd09c7c9af'
down_revision = '9d01d88aeb3f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_stat_statements extension for query performance monitoring
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")


def downgrade() -> None:
    # Drop pg_stat_statements extension
    op.execute("DROP EXTENSION IF EXISTS pg_stat_statements")
