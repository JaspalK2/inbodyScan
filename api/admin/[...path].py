import sys, os

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "services", "admin-service"))


def handler(event, context):
    """Lazy-import the real Mangum handler so Vercel build validation passes
    even before includeFiles are copied into the bundle."""
    from src.main import handler as _h
    return _h(event, context)
