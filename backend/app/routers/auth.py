from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import FeishuLoginRequest, FeishuLoginResponse, Token
from app.services.feishu_service import feishu_service


router = APIRouter(prefix="/auth", tags=["auth"])
settings = Settings()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/feishu/url")
async def get_feishu_oauth_url():
    return {"url": feishu_service.get_oauth_url()}


@router.post("/feishu/login", response_model=FeishuLoginResponse)
async def feishu_login(
    request: FeishuLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        feishu_user = await feishu_service.get_user_by_code(request.code)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    result = await db.execute(select(User).where(User.feishu_id == feishu_user["open_id"]))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            feishu_id=feishu_user["open_id"],
            name=feishu_user["name"],
            email=feishu_user.get("email"),
            phone=feishu_user.get("mobile"),
            avatar=feishu_user.get("avatar_url"),
            role="sales",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user.name = feishu_user["name"]
        if feishu_user.get("mobile"):
            user.phone = feishu_user["mobile"]
        if feishu_user.get("email"):
            user.email = feishu_user["email"]
        if feishu_user.get("avatar_url"):
            user.avatar = feishu_user["avatar_url"]
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "avatar": user.avatar,
        },
    }
