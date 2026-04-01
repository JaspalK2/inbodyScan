"""Admin-facing routes in auth-service: user listing, creation, toggling."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..schemas.auth import UserOut
from ..services.auth_service import create_user, hash_password
from ..db.session import get_db
from shared.python.auth_utils.dependencies import get_current_admin_id
from pydantic import BaseModel, EmailStr
import re

router = APIRouter(prefix="/api/auth/admin", tags=["admin-auth"])


class AdminCreateUser(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False


class ToggleActive(BaseModel):
    is_active: bool


@router.get("/users", response_model=list[UserOut])
async def list_users(_admin: str = Depends(get_current_admin_id), session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    return [UserOut.model_validate(u) for u in result.scalars().all()]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def admin_create_user(body: AdminCreateUser, _admin: str = Depends(get_current_admin_id), session: AsyncSession = Depends(get_db)):
    existing = await session.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    user = await create_user(session, body.username, body.email, body.password, body.is_admin)
    return UserOut.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserOut)
async def toggle_user(user_id: str, body: ToggleActive, _admin: str = Depends(get_current_admin_id), session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = body.is_active
    await session.commit()
    await session.refresh(user)
    return UserOut.model_validate(user)
