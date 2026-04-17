from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.security import get_password_hash
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserRead])
async def list_users(
    functional_role: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(User)
    if functional_role:
        query = query.where(User.functional_role == functional_role)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=UserRead)
async def create_user(
    user: UserCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can create users")

    existing = await db.execute(select(User).where(User.email == user.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        role=user.role,
        sales_leader_id=user.sales_leader_id,
        sales_region=user.sales_region,
        sales_product_line=user.sales_product_line,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update users")

    result = await db.execute(select(User).where(User.id == user_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    if user.name is not None:
        existing.name = user.name
    if user.email is not None:
        existing.email = user.email
    if user.role is not None:
        existing.role = user.role
    if user.sales_leader_id is not None:
        existing.sales_leader_id = user.sales_leader_id
    if user.sales_region is not None:
        existing.sales_region = user.sales_region
    if user.sales_product_line is not None:
        existing.sales_product_line = user.sales_product_line
    if user.is_active is not None:
        existing.is_active = user.is_active

    await db.commit()
    await db.refresh(existing)
    return existing


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete users")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}
