from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.permissions import assert_can_access_entity_v2, assert_can_mutate_entity_v2
from app.database import get_db
from app.models.channel import Channel
from app.models.customer import TerminalCustomer
from app.models.customer_channel_link import CustomerChannelLink
from app.schemas.customer_channel_link import (
    CustomerChannelLinkCreate,
    CustomerChannelLinkRead,
    CustomerChannelLinkUpdate,
)


router = APIRouter(prefix="/customer-channel-links", tags=["customer_channel_links"])


@router.get("/", response_model=List[CustomerChannelLinkRead])
async def list_customer_channel_links(
    customer_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required")

    query = (
        select(CustomerChannelLink, Channel.company_name, Channel.channel_code)
        .outerjoin(Channel, CustomerChannelLink.channel_id == Channel.id)
        .where(CustomerChannelLink.customer_id == customer_id)
    )

    customer_result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    await assert_can_access_entity_v2(customer, current_user, db)

    result = await db.execute(query.order_by(CustomerChannelLink.id))
    rows = result.all()
    links = []
    for row in rows:
        link = row[0]
        channel_name = row[1]
        channel_code = row[2]
        links.append(
            {
                "id": link.id,
                "customer_id": link.customer_id,
                "channel_id": link.channel_id,
                "role": link.role,
                "discount_rate": link.discount_rate,
                "start_date": link.start_date,
                "end_date": link.end_date,
                "notes": link.notes,
                "created_at": link.created_at,
                "updated_at": link.updated_at,
                "created_by": link.created_by,
                "channel_name": channel_name,
                "channel_code": channel_code,
            }
        )
    return links


@router.post("/", response_model=CustomerChannelLinkRead)
async def create_customer_channel_link(
    link: CustomerChannelLinkCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    customer_result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == link.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    await assert_can_access_entity_v2(customer, current_user, db)

    channel_result = await db.execute(select(Channel).where(Channel.id == link.channel_id))
    channel = channel_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    new_link = CustomerChannelLink(
        customer_id=link.customer_id,
        channel_id=link.channel_id,
        role=link.role,
        discount_rate=link.discount_rate,
        start_date=datetime.strptime(link.start_date, "%Y-%m-%d").date()
        if link.start_date
        else None,
        end_date=datetime.strptime(link.end_date, "%Y-%m-%d").date()
        if link.end_date
        else None,
        notes=link.notes,
        created_by=current_user["id"],
    )

    db.add(new_link)
    try:
        await db.flush()

        if link.role == "主渠道" and link.end_date is None:
            customer = await db.get(TerminalCustomer, link.customer_id)
            if customer:
                customer.channel_id = link.channel_id

        await db.commit()
        await db.refresh(new_link)
    except Exception as e:
        await db.rollback()
        if "uq_customer_active_primary_channel" in str(e):
            raise HTTPException(
                status_code=400, detail="客户已存在生效的主渠道，请先结束现有主渠道关系"
            )
        raise HTTPException(status_code=400, detail=f"创建失败: {str(e)}")

    return {
        "id": new_link.id,
        "customer_id": new_link.customer_id,
        "channel_id": new_link.channel_id,
        "role": new_link.role,
        "discount_rate": new_link.discount_rate,
        "start_date": new_link.start_date,
        "end_date": new_link.end_date,
        "notes": new_link.notes,
        "created_at": new_link.created_at,
        "updated_at": new_link.updated_at,
        "created_by": new_link.created_by,
        "channel_name": channel.company_name if channel else None,
        "channel_code": channel.channel_code if channel else None,
    }


@router.put("/{link_id}", response_model=CustomerChannelLinkRead)
async def update_customer_channel_link(
    link_id: int,
    link_update: CustomerChannelLinkUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CustomerChannelLink).where(CustomerChannelLink.id == link_id)
    )
    existing_link = result.scalar_one_or_none()
    if not existing_link:
        raise HTTPException(status_code=404, detail="Customer channel link not found")

    customer_result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == existing_link.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if customer:
        await assert_can_mutate_entity_v2(customer, current_user, db)

    update_data = link_update.model_dump(exclude_unset=True)
    original_role = existing_link.role
    original_end_date = existing_link.end_date

    for field, value in update_data.items():
        if field in ["start_date", "end_date"] and value:
            setattr(existing_link, field, datetime.strptime(value, "%Y-%m-%d").date())
        else:
            setattr(existing_link, field, value)

    try:
        await db.flush()

        customer_obj = await db.get(TerminalCustomer, existing_link.customer_id)
        if customer_obj:
            if original_role == "主渠道" and original_end_date is None:
                if existing_link.role != "主渠道" or existing_link.end_date is not None:
                    active_primary_check = await db.execute(
                        select(CustomerChannelLink).where(
                            CustomerChannelLink.customer_id == existing_link.customer_id,
                            CustomerChannelLink.role == "主渠道",
                            CustomerChannelLink.end_date.is_(None),
                            CustomerChannelLink.id != link_id,
                        )
                    )
                    active_primary = active_primary_check.scalar_one_or_none()
                    if not active_primary:
                        customer_obj.channel_id = None

            if existing_link.role == "主渠道" and existing_link.end_date is None:
                customer_obj.channel_id = existing_link.channel_id

        await db.commit()
        await db.refresh(existing_link)

        channel_result = await db.execute(
            select(Channel).where(Channel.id == existing_link.channel_id)
        )
        channel = channel_result.scalar_one_or_none()
    except Exception as e:
        await db.rollback()
        if "uq_customer_active_primary_channel" in str(e):
            raise HTTPException(
                status_code=400, detail="客户已存在生效的主渠道，请先结束现有主渠道关系"
            )
        raise HTTPException(status_code=400, detail=f"更新失败: {str(e)}")

    return {
        "id": existing_link.id,
        "customer_id": existing_link.customer_id,
        "channel_id": existing_link.channel_id,
        "role": existing_link.role,
        "discount_rate": existing_link.discount_rate,
        "start_date": existing_link.start_date,
        "end_date": existing_link.end_date,
        "notes": existing_link.notes,
        "created_at": existing_link.created_at,
        "updated_at": existing_link.updated_at,
        "created_by": existing_link.created_by,
        "channel_name": channel.company_name if channel else None,
        "channel_code": channel.channel_code if channel else None,
    }


@router.delete("/{link_id}")
async def delete_customer_channel_link(
    link_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CustomerChannelLink).where(CustomerChannelLink.id == link_id)
    )
    existing_link = result.scalar_one_or_none()
    if not existing_link:
        raise HTTPException(status_code=404, detail="Customer channel link not found")

    customer_result = await db.execute(
        select(TerminalCustomer).where(TerminalCustomer.id == existing_link.customer_id)
    )
    customer = customer_result.scalar_one_or_none()
    if customer:
        await assert_can_mutate_entity_v2(customer, current_user, db)

    if existing_link.role == "主渠道" and existing_link.end_date is None:
        customer_obj = await db.get(TerminalCustomer, existing_link.customer_id)
        if customer_obj:
            other_primary_check = await db.execute(
                select(CustomerChannelLink).where(
                    CustomerChannelLink.customer_id == existing_link.customer_id,
                    CustomerChannelLink.role == "主渠道",
                    CustomerChannelLink.end_date.is_(None),
                    CustomerChannelLink.id != link_id,
                )
            )
            other_primary = other_primary_check.scalar_one_or_none()
            if other_primary:
                customer_obj.channel_id = other_primary.channel_id
            else:
                customer_obj.channel_id = None

    await db.delete(existing_link)
    await db.commit()

    return {"message": "Customer channel link deleted successfully"}
