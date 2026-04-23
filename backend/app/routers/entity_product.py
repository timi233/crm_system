from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.policy import policy_service, build_principal
from app.database import get_db
from app.models.entity_product import EntityProduct
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.schemas.entity_product import (
    EntityProductCreate,
    EntityProductUpdate,
    EntityProductRead,
)

router = APIRouter(prefix="/entity-products", tags=["entity-products"])


async def get_entity_by_type(db: AsyncSession, entity_type: str, entity_id: int):
    if entity_type == "lead":
        result = await db.execute(select(Lead).where(Lead.id == entity_id))
        entity = result.scalar_one_or_none()
    elif entity_type == "opportunity":
        result = await db.execute(
            select(Opportunity).where(Opportunity.id == entity_id)
        )
        entity = result.scalar_one_or_none()
    elif entity_type == "project":
        result = await db.execute(select(Project).where(Project.id == entity_id))
        entity = result.scalar_one_or_none()
    else:
        raise HTTPException(status_code=400, detail="Invalid entity type")

    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_type.title()} not found")

    return entity


@router.post("/", response_model=EntityProductRead)
async def create_entity_product(
    entity_product: EntityProductCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    entity = await get_entity_by_type(
        db, entity_product.entity_type, entity_product.entity_id
    )

    await policy_service.authorize(
        resource=entity_product.entity_type,
        action="update",
        principal=principal,
        db=db,
        obj=entity,
    )

    db_entity_product = EntityProduct(**entity_product.model_dump())
    db.add(db_entity_product)
    await db.commit()
    await db.refresh(db_entity_product)
    return db_entity_product


@router.get("/{entity_product_id}", response_model=EntityProductRead)
async def get_entity_product(
    entity_product_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    result = await db.execute(
        select(EntityProduct).where(EntityProduct.id == entity_product_id)
    )
    db_entity_product = result.scalar_one_or_none()
    if not db_entity_product:
        raise HTTPException(status_code=404, detail="Entity product not found")

    entity = await get_entity_by_type(
        db, db_entity_product.entity_type, db_entity_product.entity_id
    )

    await policy_service.authorize(
        resource=db_entity_product.entity_type,
        action="read",
        principal=principal,
        db=db,
        obj=entity,
    )

    return db_entity_product


@router.put("/{entity_product_id}", response_model=EntityProductRead)
async def update_entity_product(
    entity_product_id: int,
    entity_product: EntityProductUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    result = await db.execute(
        select(EntityProduct).where(EntityProduct.id == entity_product_id)
    )
    db_entity_product = result.scalar_one_or_none()
    if not db_entity_product:
        raise HTTPException(status_code=404, detail="Entity product not found")

    entity = await get_entity_by_type(
        db, db_entity_product.entity_type, db_entity_product.entity_id
    )

    await policy_service.authorize(
        resource=db_entity_product.entity_type,
        action="update",
        principal=principal,
        db=db,
        obj=entity,
    )

    update_data = entity_product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_entity_product, field, value)

    await db.commit()
    await db.refresh(db_entity_product)
    return db_entity_product


@router.delete("/{entity_product_id}")
async def delete_entity_product(
    entity_product_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    result = await db.execute(
        select(EntityProduct).where(EntityProduct.id == entity_product_id)
    )
    db_entity_product = result.scalar_one_or_none()
    if not db_entity_product:
        raise HTTPException(status_code=404, detail="Entity product not found")

    entity = await get_entity_by_type(
        db, db_entity_product.entity_type, db_entity_product.entity_id
    )

    await policy_service.authorize(
        resource=db_entity_product.entity_type,
        action="delete",
        principal=principal,
        db=db,
        obj=entity,
    )

    await db.delete(db_entity_product)
    await db.commit()
    return {"message": "Entity product deleted successfully"}


@router.get("/", response_model=List[EntityProductRead])
async def get_entity_products(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    query = select(EntityProduct)

    if entity_type:
        query = query.where(EntityProduct.entity_type == entity_type)

    if entity_id:
        query = query.where(EntityProduct.entity_id == entity_id)

    result = await db.execute(query)
    entity_products = result.scalars().all()

    authorized_products = []
    for product in entity_products:
        try:
            entity = await get_entity_by_type(
                db, product.entity_type, product.entity_id
            )
            await policy_service.authorize(
                resource=product.entity_type,
                action="read",
                principal=principal,
                db=db,
                obj=entity,
            )
            authorized_products.append(product)
        except HTTPException:
            continue

    return authorized_products
