import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from sqlalchemy import text

from .routers.users import router as users_router
from .db.session import _engine
from shared.python.db_utils.session import Base
from .models import profile, health_goal, dietary_restriction  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with _engine.begin() as conn:
        # Create tables that don't exist yet
        await conn.run_sync(Base.metadata.create_all)
        # Ensure activity_level column exists (additive migration for existing tables)
        await conn.execute(text(
            "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS activity_level VARCHAR(30)"
        ))
    yield
    await _engine.dispose()


app = FastAPI(title="User Service", version="1.0.0", lifespan=lifespan)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/users/health")
async def health_user():
    return {"status": "ok", "service": "user"}


app.include_router(users_router)

handler = Mangum(app, lifespan="off")
