import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models
from services.auth_service.src.models.user import User  # noqa
from services.auth_service.src.models.refresh_token import RefreshToken  # noqa
from shared.python.db_utils.session import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = os.environ["AUTH_DATABASE_URL"]
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    url = os.environ["AUTH_DATABASE_URL"]
    connectable = create_async_engine(url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
