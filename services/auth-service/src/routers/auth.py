from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.auth import (
    LoginRequest, RegisterRequest, TokenResponse, UserOut, RefreshRequest,
    GoogleLoginRequest, GoogleLinkResponse, ConfirmLinkRequest,
)
from ..services.auth_service import (
    create_user, get_user_by_username, get_user_by_id, get_user_by_email,
    get_user_by_google_sub, create_google_user, link_google_account,
    verify_password, create_access_token, create_refresh_token_value,
    store_refresh_token, validate_refresh_token, revoke_refresh_token,
)
from ..services.google_auth_service import (
    verify_google_token, create_link_request, resolve_link_request,
)
from ..db.session import get_db
from shared.python.auth_utils.dependencies import get_current_user_id

router = APIRouter(prefix="/api/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60        # 7 days — password login sessions
GOOGLE_REFRESH_COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days — Google login sessions (SC-007)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, session: AsyncSession = Depends(get_db)):
    user = await get_user_by_username(session, body.username)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    access_token = create_access_token(user.id, user.is_admin)
    refresh_token = create_refresh_token_value()
    await store_refresh_token(session, user.id, refresh_token)

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=COOKIE_MAX_AGE,
    )
    return TokenResponse(access_token=access_token)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_db)):
    existing = await get_user_by_username(session, body.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    existing_email = await get_user_by_email(session, body.email)
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = await create_user(session, body.username, body.email, body.password)
    return UserOut.model_validate(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    session: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    rt = await validate_refresh_token(session, refresh_token)
    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user = await get_user_by_id(session, rt.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or disabled")

    await revoke_refresh_token(session, refresh_token)
    new_refresh = create_refresh_token_value()
    await store_refresh_token(session, user.id, new_refresh)

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=new_refresh,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=COOKIE_MAX_AGE,
    )
    return TokenResponse(access_token=create_access_token(user.id, user.is_admin))


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    session: AsyncSession = Depends(get_db),
):
    if refresh_token:
        await revoke_refresh_token(session, refresh_token)
    response.delete_cookie(REFRESH_COOKIE)
    return {"detail": "Logged out"}


@router.post("/google")
async def google_login(
    body: GoogleLoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    """Sign in or register via a Google-issued ID token.

    Lookup priority (T023 — constitution comment):
    1. google_sub  — reliable even if user changes Google email
    2. email       — used for new-user creation and conflict detection
    If an existing password-based account has the same email, a link-confirmation
    flow is started (202) instead of issuing a session.
    """
    try:
        payload = verify_google_token(body.id_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    google_sub: str = payload["sub"]
    email: str = payload.get("email", "")
    google_name: str | None = payload.get("name")

    # 1. Look up by google_sub first (handles email-change scenario)
    user = await get_user_by_google_sub(session, google_sub)

    if user is None:
        # 2. Look up by email
        user = await get_user_by_email(session, email)
        if user is not None and user.google_sub is None:
            # Existing password-based account — require confirmation before linking
            link_token = await create_link_request(session, email, google_sub, google_name)
            return GoogleLinkResponse(link_token=link_token, email=email, google_name=google_name)

    if user is not None and not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    is_new_user = user is None
    if is_new_user:
        user = await create_google_user(session, email, google_sub)

    access_token = create_access_token(user.id, user.is_admin)
    refresh_token_value = create_refresh_token_value()
    await store_refresh_token(session, user.id, refresh_token_value, expire_days=30)

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token_value,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=GOOGLE_REFRESH_COOKIE_MAX_AGE,  # 30-day rolling session (SC-007)
    )

    response.status_code = status.HTTP_201_CREATED if is_new_user else status.HTTP_200_OK
    return TokenResponse(access_token=access_token)


@router.post("/google/confirm-link", response_model=TokenResponse)
async def google_confirm_link(
    body: ConfirmLinkRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    """Complete account linking after user confirms the prompt."""
    link_req = await resolve_link_request(session, body.link_token)
    if link_req is None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Link request expired or not found. Please sign in with Google again.",
        )

    user = await get_user_by_email(session, link_req.email)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or disabled")

    await link_google_account(session, user.id, link_req.google_sub)

    access_token = create_access_token(user.id, user.is_admin)
    refresh_token_value = create_refresh_token_value()
    await store_refresh_token(session, user.id, refresh_token_value, expire_days=30)

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token_value,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=GOOGLE_REFRESH_COOKIE_MAX_AGE,
    )
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def me(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut.model_validate(user)
