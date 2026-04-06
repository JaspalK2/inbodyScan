import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from .routers.analytics import router as analytics_router
from .db.session import _engine
from shared.python.db_utils.session import Base
from .models import dashboard_cache  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are managed via Supabase / Alembic migrations — skip create_all
    yield
    await _engine.dispose()


app = FastAPI(title="Analytics Service", version="1.0.0", lifespan=lifespan)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/analytics/health")
async def health_analytics():
    return {"status": "ok", "service": "analytics"}


app.include_router(analytics_router)

handler = Mangum(app, lifespan="off")
