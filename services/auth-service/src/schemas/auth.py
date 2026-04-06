from pydantic import BaseModel, EmailStr, field_validator
import re


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("username")
    @classmethod
    def username_format(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,64}$", v):
            raise ValueError("Username must be 3-64 alphanumeric characters or underscores")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    is_admin: bool
    is_active: bool
    google_sub: str | None = None

    model_config = {"from_attributes": True}


class GoogleLoginRequest(BaseModel):
    id_token: str


class GoogleLinkResponse(BaseModel):
    link_token: str
    email: str
    google_name: str | None = None


class ConfirmLinkRequest(BaseModel):
    link_token: str
