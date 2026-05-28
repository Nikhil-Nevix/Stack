from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel
from typing import Optional
from ....core.database import get_db
from ....core.security import (
    verify_password, create_access_token, validate_jadeglobal_domain,
    get_current_user
)
from ....models.user import User

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    department: Optional[str] = None
    device_name: Optional[str] = None
    is_active: bool
    last_login: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    validate_jadeglobal_domain(data.email)
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials. Please try again.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been deactivated.")

    await db.execute(
        update(User).where(User.user_id == user.user_id).values(last_login=datetime.now(timezone.utc))
    )
    await db.commit()

    token = create_access_token({"user_id": user.user_id, "email": user.email, "role": user.role, "name": user.full_name})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department,
            "device_name": user.device_name,
            "is_active": user.is_active,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat()
        }
    }


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "department": current_user.department,
        "device_name": current_user.device_name,
        "is_active": current_user.is_active,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "created_at": current_user.created_at.isoformat()
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}
