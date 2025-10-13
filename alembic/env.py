"""
Alembic environment configuration.
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import settings and Base
from app.core.config import settings
from app.db.session import Base

# Import all models here to ensure they're registered with Base.metadata
# from app.models.user import User
# from app.models.article import Article
# from app.models.rss_source import RSSSource
# from app.models.vote import Vote
# from app.models.comment import Comment

# this is the Alembic Config object
config = context.config

# We'll set the URL directly in run_migrations_online() to avoid ConfigParser issues
# with URL-encoded passwords containing %

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Get URL directly from settings to avoid ConfigParser issues
    url = settings.DATABASE_URL.replace("+asyncpg", "")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with sync engine."""
    # Get URL directly from settings and create engine without ConfigParser
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    
    from sqlalchemy import create_engine
    connectable = create_engine(
        sync_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
