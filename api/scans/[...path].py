import sys, os

# Go up 2 dirs from api/<svc>/ to reach repo root
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "services", "scan-service"))


class _LazyASGI:
    """Defers service import until first request so Vercel build validation passes."""

    _real = None

    async def __call__(self, scope, receive, send):
        if self._real is None:
            from src.main import app as _app
            self._real = _app
        await self._real(scope, receive, send)


app = _LazyASGI()
