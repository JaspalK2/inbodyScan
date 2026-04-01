import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.profile import UserProfile
from ..models.health_goal import HealthGoal
from ..models.dietary_restriction import DietaryRestriction


async def get_or_create_profile(session: AsyncSession, user_id: str) -> UserProfile:
    result = await session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(id=str(uuid.uuid4()), user_id=user_id)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
    return profile


async def update_profile(session: AsyncSession, user_id: str, data: dict) -> UserProfile:
    profile = await get_or_create_profile(session, user_id)
    for key, value in data.items():
        if value is not None:
            setattr(profile, key, value)
    await session.commit()
    await session.refresh(profile)
    return profile


async def get_health_goal(session: AsyncSession, user_id: str) -> HealthGoal | None:
    result = await session.execute(select(HealthGoal).where(HealthGoal.user_id == user_id))
    return result.scalar_one_or_none()


async def set_health_goal(session: AsyncSession, user_id: str, goal_type: str) -> HealthGoal:
    goal = await get_health_goal(session, user_id)
    if goal:
        goal.goal_type = goal_type
    else:
        goal = HealthGoal(id=str(uuid.uuid4()), user_id=user_id, goal_type=goal_type)
        session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return goal


async def get_dietary_restrictions(session: AsyncSession, user_id: str) -> list[DietaryRestriction]:
    result = await session.execute(
        select(DietaryRestriction).where(DietaryRestriction.user_id == user_id)
    )
    return list(result.scalars().all())


async def add_dietary_restriction(session: AsyncSession, user_id: str, restriction_type: str, notes: str | None) -> DietaryRestriction:
    dr = DietaryRestriction(
        id=str(uuid.uuid4()),
        user_id=user_id,
        restriction_type=restriction_type,
        notes=notes,
    )
    session.add(dr)
    await session.commit()
    await session.refresh(dr)
    return dr


async def remove_dietary_restriction(session: AsyncSession, user_id: str, restriction_id: str) -> bool:
    result = await session.execute(
        select(DietaryRestriction).where(
            DietaryRestriction.id == restriction_id,
            DietaryRestriction.user_id == user_id,
        )
    )
    dr = result.scalar_one_or_none()
    if not dr:
        return False
    await session.delete(dr)
    await session.commit()
    return True
