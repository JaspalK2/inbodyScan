"""Async SQLAlchemy session factory for asyncpg (Supabase PostgreSQL)."""
import os
from typing import AsyncGenerator
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


def make_engine(database_url_env: str):
    url = os.environ[database_url_env]
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
