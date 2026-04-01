"""Async SQLAlchemy session factory for asyncpg (Supabase PostgreSQL)."""
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


def make_engine(database_url_env: str):
    url = os.environ[database_url_env]
    return create_async_engine(
        url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        echo=False,
        # Supabase uses pgbouncer in transaction mode which does not support
        # prepared statements — disable asyncpg's statement cache entirely.
        connect_args={"statement_cache_size": 0},
    )


def make_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
