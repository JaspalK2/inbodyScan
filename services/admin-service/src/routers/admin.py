from fastapi import APIRouter, Depends, HTTPException, Request, status
from ..schemas.admin import CreateUserRequest, UserAdminOut, ToggleActiveRequest
from ..services.admin_service import create_user, list_users, toggle_user_active
from shared.python.auth_utils.dependencies import get_current_admin_id

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _get_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    return auth[7:]


@router.get("/users", response_model=list[UserAdminOut])
async def list_all_users(request: Request, _admin: str = Depends(get_current_admin_id)):
    token = _get_token(request)
    return await list_users(token)


@router.post("/users", response_model=UserAdminOut, status_code=status.HTTP_201_CREATED)
async def create_new_user(body: CreateUserRequest, request: Request, _admin: str = Depends(get_current_admin_id)):
    token = _get_token(request)
    return await create_user(token, body.username, body.email, body.password, body.is_admin)


@router.patch("/users/{user_id}", response_model=UserAdminOut)
async def toggle_active(user_id: str, body: ToggleActiveRequest, request: Request, _admin: str = Depends(get_current_admin_id)):
    token = _get_token(request)
    return await toggle_user_active(token, user_id, body.is_active)
