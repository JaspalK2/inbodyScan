"""Admin service delegates user creation/management to the auth-service via HTTP."""
import os
import httpx

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8001")


async def create_user(token: str, username: str, email: str, password: str, is_admin: bool) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{AUTH_SERVICE_URL}/api/auth/admin/users",
            json={"username": username, "email": email, "password": password, "is_admin": is_admin},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


async def list_users(token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{AUTH_SERVICE_URL}/api/auth/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


async def toggle_user_active(token: str, user_id: str, is_active: bool) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{AUTH_SERVICE_URL}/api/auth/admin/users/{user_id}",
            json={"is_active": is_active},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()
