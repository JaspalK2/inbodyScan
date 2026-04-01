from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.analytics import DashboardResponse, MetricHistory
from ..services.analytics_service import build_dashboard
from ..db.session import get_db
from shared.python.auth_utils.dependencies import get_current_user_id

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return await build_dashboard(session, user_id)
