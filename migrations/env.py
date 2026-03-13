import asyncio
import os
import ssl
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine
from alembic import context
from dotenv import load_dotenv

load_dotenv()

from database.models import Base

config = context.config

# .env dan DATABASE_URL olish va asyncpg formatiga o'tkazish
db_url = os.getenv("DATABASE_URL", "")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    # Lokal PostgreSQL uchun SSL kerak emas
    is_local = "localhost" in db_url or "127.0.0.1" in db_url
    connect_args = {} if is_local else {"ssl": ssl.create_default_context()}

    connectable = create_async_engine(
        db_url,
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
