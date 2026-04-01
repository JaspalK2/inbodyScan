from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from shared.python.db_utils.session import make_engine, make_session_factory

_engine = make_engine("USER_DATABASE_URL")
_session_factory = make_session_factory(_engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session
