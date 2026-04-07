import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from .routers.scans import router as scans_router
from .db.session import _engine
from shared.python.db_utils.session import Base
from .models import scan, metric  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass
    yield
    await _engine.dispose()


app = FastAPI(title="Scan Service", version="1.0.0", lifespan=lifespan)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/scans/health")
async def health_scan():
    return {"status": "ok", "service": "scan"}


app.include_router(scans_router)

handler = Mangum(app, lifespan="off")
