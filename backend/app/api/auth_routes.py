from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.role_schema import RegisterRequest, LoginRequest, ProfileUpdateRequest
from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_user_by_id,
)
from app.db.database import get_db_connection

router = APIRouter(tags=["Phase 8 — Authentication & Profile"])


@router.post("/auth/register", status_code=status.HTTP_201_CREATED, summary="Register User Account")
async def register(req: RegisterRequest):
    try:
        user = register_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            phone=req.phone,
            role=req.role,
            assigned_state=req.assigned_state,
            assigned_district=req.assigned_district,
            provision_secret=req.provision_secret,
        )
        token = create_access_token(user)
        return {"success": True, "access_token": token, "token_type": "bearer", "user": user}
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/auth/login", summary="Login and Obtain JWT Access Token")
async def login(req: LoginRequest):
    user = authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    token = create_access_token(user)
    return {"success": True, "access_token": token, "token_type": "bearer", "user": user}


@router.get("/users/me", summary="Get Current Authenticated User Profile")
async def get_my_profile(user: dict = Depends(get_current_user)):
    return user


@router.patch("/users/me", summary="Update Profile Name/Phone (Role Cannot Be Self-Changed)")
async def update_my_profile(req: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    sets = []
    params = []
    if req.full_name is not None:
        sets.append("full_name = ?")
        params.append(req.full_name.strip())
    if req.phone is not None:
        sets.append("phone = ?")
        params.append(req.phone.strip())
    if sets:
        params.append(user["user_id"])
        conn = get_db_connection()
        try:
            conn.execute(f"UPDATE users SET {', '.join(sets)} WHERE user_id = ?", tuple(params))
            conn.commit()
        finally:
            conn.close()
    return get_user_by_id(user["user_id"])
