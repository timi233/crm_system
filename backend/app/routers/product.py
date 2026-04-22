from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.policy import build_principal, policy_service
from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate


router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductRead])
async def list_products(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    query = await policy_service.scope_query(
        resource="product",
        action="list",
        principal=principal,
        db=db,
        query=select(Product),
        model=Product,
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=ProductRead)
async def create_product(
    product: ProductCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize_create(
        resource="product",
        principal=principal,
        db=db,
        payload=product,
    )

    count_result = await db.execute(select(Product.id))
    count = len(count_result.scalars().all()) + 1
    product_code = f"PRD-{count:03d}"

    new_product = Product(
        product_code=product_code,
        product_name=product.product_name,
        product_type=product.product_type,
        brand_manufacturer=product.brand_manufacturer,
        is_active=product.is_active,
        notes=product.notes,
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="product",
        action="update",
        principal=principal,
        db=db,
        obj=existing,
    )

    if product.product_name is not None:
        existing.product_name = product.product_name
    if product.product_type is not None:
        existing.product_type = product.product_type
    if product.brand_manufacturer is not None:
        existing.brand_manufacturer = product.brand_manufacturer
    if product.is_active is not None:
        existing.is_active = product.is_active
    if product.notes is not None:
        existing.notes = product.notes

    await db.commit()
    await db.refresh(existing)
    return existing


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="product",
        action="delete",
        principal=principal,
        db=db,
        obj=product,
    )

    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted successfully"}
