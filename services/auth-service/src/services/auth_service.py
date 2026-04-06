"""Business logic for authentication: password hashing, token generation, user creation."""
import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..models.refresh_token import RefreshToken

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "placeholder-secret-for-build")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, is_admin: bool) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "is_admin": is_admin, "exp": expire, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token_value() -> str:
    return str(uuid.uuid4()) + str(uuid.uuid4())


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_user(session: AsyncSession, username: str, email: str, password: str, is_admin: bool = False) -> User:
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        hashed_password=hash_password(password),
        is_admin=is_admin,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_google_sub(session: AsyncSession, sub: str) -> User | None:
    result = await session.execute(select(User).where(User.google_sub == sub))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_google_user(session: AsyncSession, email: str, google_sub: str) -> User:
    """Create a new user from a verified Google identity.

    Username is auto-generated as google_<first 8 chars of sub>.
    hashed_password is None — Google-only accounts have no password.
    """
    username = f"google_{google_sub[:8]}"
    # Ensure username uniqueness by appending a suffix if needed
    base_username = username
    suffix = 1
    while await get_user_by_username(session, username):
        username = f"{base_username}_{suffix}"
        suffix += 1

    user = User(
        id=str(uuid.uuid4()),
        username=username,
        email=email,
        hashed_password=None,
        google_sub=google_sub,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def link_google_account(session: AsyncSession, user_id: str, google_sub: str) -> User:
    """Link a Google identity to an existing user account by setting google_sub."""
    user = await get_user_by_id(session, user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    user.google_sub = google_sub
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def store_refresh_token(
    session: AsyncSession, user_id: str, token: str, expire_days: int | None = None
) -> RefreshToken:
    days = expire_days if expire_days is not None else REFRESH_TOKEN_EXPIRE_DAYS
    expires = datetime.now(timezone.utc) + timedelta(days=days)
    rt = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=expires,
    )
    session.add(rt)
    await session.commit()
    return rt


async def validate_refresh_token(session: AsyncSession, token: str) -> RefreshToken | None:
    token_hash = hash_token(token)
    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(session: AsyncSession, token: str) -> None:
    rt = await validate_refresh_token(session, token)
    if rt:
        await session.delete(rt)
        await session.commit()
