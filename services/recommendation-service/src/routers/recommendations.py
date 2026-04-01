from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.recommendation import (
    GenerateDietRequest, GenerateWorkoutRequest,
    DietRecommendationOut, WorkoutRecommendationOut,
)
from ..services.recommendation_service import (
    generate_diet_recommendation, generate_workout_recommendation,
    get_diet_recommendations, get_workout_recommendations,
)
from ..db.session import get_db
from shared.python.auth_utils.dependencies import get_current_user_id

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("/diet/generate", response_model=DietRecommendationOut, status_code=status.HTTP_201_CREATED)
async def generate_diet(
    body: GenerateDietRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    """Synchronous generation — completes in ~8s, within Vercel 60s timeout."""
    return await generate_diet_recommendation(
        session, user_id, body.scan_id, body.metrics, body.goal_type, body.dietary_restrictions
    )


@router.post("/workout/generate", response_model=WorkoutRecommendationOut, status_code=status.HTTP_201_CREATED)
async def generate_workout(
    body: GenerateWorkoutRequest,
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db),
):
    return await generate_workout_recommendation(
        session, user_id, body.scan_id, body.metrics, body.goal_type
    )


@router.get("/diet", response_model=list[DietRecommendationOut])
async def list_diet(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return await get_diet_recommendations(session, user_id)


@router.get("/workout", response_model=list[WorkoutRecommendationOut])
async def list_workout(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return await get_workout_recommendations(session, user_id)
