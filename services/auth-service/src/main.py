"""Auth-service entry point. Exposes `handler` for Vercel (Mangum) and `app` for local uvicorn."""
import os
import sys

# Allow imports from repo root (for shared/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from .routers.auth import router as auth_router
from .routers.admin import router as admin_router
from .db.session import _engine
from shared.python.db_utils.session import Base

# Import models so Alembic and create_all can find them
from .models import user, refresh_token, google_link_request  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are managed via Supabase / Alembic migrations — skip create_all
    await _seed_admin()
    yield
    await _engine.dispose()


async def _seed_admin():
    admin_username = os.environ.get("INITIAL_ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("INITIAL_ADMIN_PASSWORD", "")
    if not admin_password:
        return

    from .db.session import _session_factory
    from .services.auth_service import get_user_by_username, create_user

    async with _session_factory() as session:
        existing = await get_user_by_username(session, admin_username)
        if not existing:
            await create_user(
                session,
                username=admin_username,
                email=f"{admin_username}@inbody.local",
                password=admin_password,
                is_admin=True,
            )


app = FastAPI(title="Auth Service", version="1.0.0", lifespan=lifespan)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/auth/health")
async def health_auth():
    return {"status": "ok", "service": "auth"}


app.include_router(auth_router)
app.include_router(admin_router)

# Vercel serverless handler
handler = Mangum(app, lifespan="off")
