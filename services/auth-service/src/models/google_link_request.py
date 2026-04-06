import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from shared.python.db_utils.session import Base


class GoogleLinkRequest(Base):
    """Transient record holding a pending Google account-link confirmation.

    Created when a Google sign-in email matches an existing password-based account.
    Expires after 10 minutes. Deleted on resolution (confirm or decline).
    """

    __tablename__ = "google_link_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Opaque token returned to the frontend; used to confirm or cancel the link
    state_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    # Email of the existing account that would be linked
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    # Google subject identifier from the verified ID token
    google_sub: Mapped[str] = mapped_column(String(255), nullable=False)
    # Display name from Google profile (shown in confirmation UI)
    google_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
