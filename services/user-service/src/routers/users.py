from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.user import (
    ProfileOut, ProfileUpdate, HealthGoalSet, HealthGoalOut,
    DietaryRestrictionAdd, DietaryRestrictionOut,
)
from ..services.user_service import (
    get_or_create_profile, update_profile,
    get_health_goal, set_health_goal,
    get_dietary_restrictions, add_dietary_restriction, remove_dietary_restriction,
)
from ..db.session import get_db
from shared.python.auth_utils.dependencies import get_current_user_id

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me/profile", response_model=ProfileOut)
async def get_profile(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return await get_or_create_profile(session, user_id)


@router.patch("/me/profile", response_model=ProfileOut)
async def patch_profile(body: ProfileUpdate, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return await update_profile(session, user_id, body.model_dump(exclude_none=True))


@router.get("/me/goal", response_model=HealthGoalOut | None)
async def get_goal(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return await get_health_goal(session, user_id)


@router.put("/me/goal", response_model=HealthGoalOut)
async def set_goal(body: HealthGoalSet, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return await set_health_goal(session, user_id, body.goal_type)


@router.get("/me/dietary-restrictions", response_model=list[DietaryRestrictionOut])
async def list_restrictions(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return await get_dietary_restrictions(session, user_id)


@router.post("/me/dietary-restrictions", response_model=DietaryRestrictionOut, status_code=status.HTTP_201_CREATED)
async def add_restriction(body: DietaryRestrictionAdd, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return await add_dietary_restriction(session, user_id, body.restriction_type, body.notes)


@router.delete("/me/dietary-restrictions/{restriction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restriction(restriction_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    deleted = await remove_dietary_restriction(session, user_id, restriction_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restriction not found")
