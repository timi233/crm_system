from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.policy.service import build_principal, policy_service
from app.database import get_db
from app.models.dict_item import DictItem
from app.schemas.dict_item import DictItemCreate, DictItemRead, DictItemUpdate


router = APIRouter(tags=["dict_items"])


@router.get("/dict/items", response_model=List[DictItemRead])
async def list_dict_items(
    dict_type: Optional[str] = None,
    parent_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="dict_item",
        action="list",
        principal=principal,
        db=db,
        obj=None,
    )
    query = select(DictItem)
    if dict_type:
        query = query.where(DictItem.dict_type == dict_type)
    if parent_id is not None:
        query = query.where(DictItem.parent_id == parent_id)
    query = query.order_by(DictItem.sort_order, DictItem.id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/dict/types")
async def list_dict_types(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="dict_item",
        action="list",
        principal=principal,
        db=db,
        obj=None,
    )
    result = await db.execute(
        select(DictItem.dict_type).distinct().order_by(DictItem.dict_type)
    )
    return {"types": result.scalars().all()}


@router.get("/dict-items/brands")
async def list_brands(
    product_type_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="dict_item",
        action="list",
        principal=principal,
        db=db,
        obj=None,
    )
    query = select(DictItem).where(
        DictItem.dict_type.in_(["brand", "product_brand", "产品品牌"])
    )
    if product_type_id is not None:
        type_item = await db.execute(select(DictItem).where(DictItem.id == product_type_id))
        type_result = type_item.scalar_one_or_none()

        if type_result and type_result.parent_id is None:
            child_types = await db.execute(
                select(DictItem.id).where(DictItem.parent_id == product_type_id)
            )
            child_ids = [row[0] for row in child_types.fetchall()]
            all_ids = child_ids + [product_type_id]
            query = query.where(DictItem.parent_id.in_(all_ids))
        else:
            query = query.where(DictItem.parent_id == product_type_id)

    query = query.where(DictItem.is_active == True).order_by(
        DictItem.sort_order, DictItem.id
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/dict-items/models")
async def list_models(
    brand_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="dict_item",
        action="list",
        principal=principal,
        db=db,
        obj=None,
    )
    query = select(DictItem).where(DictItem.dict_type.in_(["model", "产品型号"]))
    if brand_id is not None:
        query = query.where(DictItem.parent_id == brand_id)
    query = query.where(DictItem.is_active == True).order_by(
        DictItem.sort_order, DictItem.id
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/dict-items/product-types")
async def list_product_types(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="dict_item",
        action="list",
        principal=principal,
        db=db,
        obj=None,
    )
    query = select(DictItem).where(DictItem.dict_type.in_(["product_type", "产品类型"]))
    query = query.where(DictItem.is_active == True).order_by(
        DictItem.sort_order, DictItem.id
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/dict/items", response_model=DictItemRead)
async def create_dict_item(
    item: DictItemCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize_create(
        resource="dict_item",
        principal=principal,
        db=db,
        payload=item,
    )

    new_item = DictItem(
        dict_type=item.dict_type,
        code=item.code,
        name=item.name,
        parent_id=item.parent_id,
        sort_order=item.sort_order,
        is_active=item.is_active,
        extra_data=item.extra_data,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


@router.put("/dict/items/{item_id}", response_model=DictItemRead)
async def update_dict_item(
    item_id: int,
    item: DictItemUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    result = await db.execute(select(DictItem).where(DictItem.id == item_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Dict item not found")

    await policy_service.authorize(
        resource="dict_item",
        action="update",
        principal=principal,
        db=db,
        obj=existing,
    )

    if item.code is not None:
        existing.code = item.code
    if item.name is not None:
        existing.name = item.name
    if item.parent_id is not None:
        existing.parent_id = item.parent_id
    if item.sort_order is not None:
        existing.sort_order = item.sort_order
    if item.is_active is not None:
        existing.is_active = item.is_active
    if item.extra_data is not None:
        existing.extra_data = item.extra_data

    await db.commit()
    await db.refresh(existing)
    return existing


@router.delete("/dict/items/{item_id}")
async def delete_dict_item(
    item_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    result = await db.execute(select(DictItem).where(DictItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Dict item not found")

    await policy_service.authorize(
        resource="dict_item",
        action="delete",
        principal=principal,
        db=db,
        obj=item,
    )

    await db.delete(item)
    await db.commit()
    return {"message": "Dict item deleted successfully"}
