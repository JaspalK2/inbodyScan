"""Google OAuth ID token verification and account-link request management."""
import os
import secrets
from datetime import datetime, timedelta, timezone

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.google_link_request import GoogleLinkRequest

LINK_REQUEST_TTL_MINUTES = 10


def verify_google_token(raw_id_token: str) -> dict:
    """Verify a Google-issued ID token server-side.

    Returns the decoded token payload dict on success.
    Raises ValueError if verification fails (expired, wrong audience, invalid signature).

    IMPORTANT (constitution Principle — no PII in logs):
    Do NOT log raw_id_token or the returned email/sub at any log level.
    """
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID environment variable is not set")

    try:
        payload = google_id_token.verify_oauth2_token(
            raw_id_token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except Exception as exc:
        raise ValueError(f"Google token verification failed: {type(exc).__name__}") from exc

    # verify_oauth2_token already checks aud, but be explicit
    if payload.get("aud") != GOOGLE_CLIENT_ID:
        raise ValueError("Google token audience mismatch")

    return payload


async def create_link_request(
    session: AsyncSession,
    email: str,
    google_sub: str,
    google_name: str | None,
) -> str:
    """Store a pending account-link confirmation record.

    Returns the opaque state_token to send to the frontend.
    The record expires after LINK_REQUEST_TTL_MINUTES minutes.
    """
    state_token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=LINK_REQUEST_TTL_MINUTES)
    link_req = GoogleLinkRequest(
        state_token=state_token,
        email=email,
        google_sub=google_sub,
        google_name=google_name,
        expires_at=expires_at,
    )
    session.add(link_req)
    await session.commit()
    return state_token


async def resolve_link_request(
    session: AsyncSession,
    state_token: str,
) -> GoogleLinkRequest | None:
    """Fetch and delete a valid (non-expired) link request by state_token.

    Returns the GoogleLinkRequest if found and not expired, otherwise None.
    The record is deleted on successful resolution to prevent reuse.
    """
    result = await session.execute(
        select(GoogleLinkRequest).where(
            GoogleLinkRequest.state_token == state_token,
            GoogleLinkRequest.expires_at > datetime.now(timezone.utc),
        )
    )
    link_req = result.scalar_one_or_none()
    if link_req is None:
        return None
    await session.delete(link_req)
    await session.commit()
    return link_req
