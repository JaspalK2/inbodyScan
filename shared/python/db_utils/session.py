"""Async SQLAlchemy session factory for asyncpg (Supabase PostgreSQL)."""
import os
from typing import AsyncGenerator
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


def make_engine(database_url_env: str):
    # Fall back to DATABASE_URL so all services work with a single Vercel env var.
    # Use a dummy URL at build/import time if neither is set (no DB connection
    # is made until the first actual query, so this is safe).
    url = (
        os.environ.get(database_url_env)
        or os.environ.get("DATABASE_URL")
        or "postgresql+asyncpg://user:pass@localhost/db"
    )
    # Supabase uses pgbouncer in transaction mode.
    # Fix: use UUID-based prepared statement names (avoids sequential collisions)
    # and NullPool so SQLAlchemy doesn't reuse connections across requests.
    return create_async_engine(
        url,
        poolclass=NullPool,
        echo=False,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
        },
    )


def make_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
