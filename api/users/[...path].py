import sys, os

# Go up 2 dirs from api/<svc>/ to reach repo root
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "services", "user-service"))


class _LazyASGI:
    """Defers service import until first request so Vercel build validation passes."""

    _real = None
    _db_initialized = False

    async def __call__(self, scope, receive, send):
        if self._real is None:
            from src.main import app as _app
            self._real = _app
        if not self._db_initialized and scope.get("type") == "http":
            self._db_initialized = True
            try:
                from src.db.session import _engine
                from shared.python.db_utils.session import Base
                from sqlalchemy import text
                import src.models.profile  # noqa
                import src.models.health_goal  # noqa
                import src.models.dietary_restriction  # noqa
                async with _engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                    await conn.execute(text(
                        "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS activity_level VARCHAR(30)"
                    ))
            except Exception:
                pass
        await self._real(scope, receive, send)


app = _LazyASGI()
