import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .routers.recommendations import router as rec_router
from .db.session import _engine

# Import all models so SQLAlchemy metadata is populated
from .models import diet_recommendation, workout_recommendation, nutritional_food  # noqa
from .models import custom_meal, day_plan, workout_split  # noqa
from .models import food_log  # noqa

logger = logging.getLogger(__name__)
_scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start weekly food DB refresh scheduler (Sunday 02:00 UTC)
    usda_key = os.environ.get("USDA_API_KEY", "")
    if usda_key:
        from .services.food_seeder import refresh_food_db_job
        _scheduler.add_job(refresh_food_db_job, "cron", day_of_week="sun", hour=2, minute=0, id="food_db_refresh")
        _scheduler.start()
        logger.info("Food DB refresh scheduler started (weekly, Sunday 02:00 UTC)")
    else:
        logger.info("USDA_API_KEY not set — food DB auto-refresh disabled")
    yield
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
    await _engine.dispose()


app = FastAPI(title="Recommendation Service", version="2.0.0", lifespan=lifespan)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
@app.get("/api/recommendations/health")
async def health_rec():
    return {"status": "ok", "service": "recommendation"}


app.include_router(rec_router)

handler = Mangum(app, lifespan="off")
