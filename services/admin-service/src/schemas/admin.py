from pydantic import BaseModel, EmailStr, field_validator
import re


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    is_admin: bool = False

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


class UserAdminOut(BaseModel):
    id: str
    username: str
    email: str
    is_admin: bool
    is_active: bool


class ToggleActiveRequest(BaseModel):
    is_active: bool
