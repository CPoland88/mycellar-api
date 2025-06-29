"""
Alembic migration environment for CellarCore
(Replace existing migrations/env.py with this content)
"""
from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

# --------------------------------------------------------
# 1) Read DATABASE_URL, or fall back to local SQLite file
# --------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cellar.db")

# --------------------------------------------------------
# 2) Alembic Config object
# --------------------------------------------------------
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)   # ★ key line ★

# --------------------------------------------------------
# 3) Configure Python logging (optional but standard)
# --------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --------------------------------------------------------
# 4) Import model metadata for 'autogenerate'
# --------------------------------------------------------
from app.models import SQLModel          # noqa: E402  (late import)
target_metadata = SQLModel.metadata

# --------------------------------------------------------
# 5) Two run modes: 'offline' (emit SQL) and 'online' (run)
# --------------------------------------------------------
def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,          # detect column-type changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
