import sys, os, traceback

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, repo_root)
sys.path.insert(0, os.path.join(repo_root, 'services', 'scan-service'))

try:
    from src.main import handler
except Exception:
    import traceback as _tb
    _err = _tb.format_exc()
    from mangum import Mangum
    from fastapi import FastAPI
    _app = FastAPI()
    @_app.api_route("/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"])
    async def _error(path: str = ""):
        return {"error": "Import failed", "detail": _err}
    handler = Mangum(_app, lifespan="off")
