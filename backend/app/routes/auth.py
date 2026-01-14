import os
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config import get_settings
from ..database import get_db
from ..models.user import User, UserResponse, Token
from ..auth.security import (
    verify_password,
    create_access_token,
    get_current_user,
    get_password_hash,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Find user
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return current_user


@router.post("/logout")
async def logout():
    # With JWT, logout is handled client-side by removing the token
    return {"message": "Successfully logged out"}


@router.post("/setup")
async def setup_admin(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create or reset the admin user using DEFAULT_ADMIN_EMAIL and DEFAULT_ADMIN_PASSWORD env vars.
    This endpoint is only available if those env vars are set.
    """
    admin_email = os.environ.get("DEFAULT_ADMIN_EMAIL")
    admin_password = os.environ.get("DEFAULT_ADMIN_PASSWORD")

    if not admin_email or not admin_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="DEFAULT_ADMIN_EMAIL and DEFAULT_ADMIN_PASSWORD env vars must be set"
        )

    # Strip whitespace from email and password
    admin_email = admin_email.strip()
    admin_password = admin_password.strip()

    # Check if user exists
    result = await db.execute(select(User).where(User.email == admin_email))
    user = result.scalar_one_or_none()

    if user:
        # Update password
        user.hashed_password = get_password_hash(admin_password)
        await db.commit()
        return {"message": f"Password updated for {admin_email}"}
    else:
        # Create user
        new_user = User(
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            is_active=True,
        )
        db.add(new_user)
        await db.commit()
        return {"message": f"User created: {admin_email}"}
