from typing import Any
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..types import Resource, Action
from ..context import PrincipalContext
from ..helpers import (
    get_assigned_channel_ids,
    get_technician_related_project_ids,
    has_full_access,
)
from fastapi import HTTPException


class ContractPolicy(BasePolicy):
    resource: Resource = "contract"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: Action = "list",
    ) -> Any:
        if principal.role in {"admin", "business", "finance"}:
            return query

        if principal.is_sales:
            from app.models.customer import TerminalCustomer
            from app.models.project import Project

            assigned_channels = await get_assigned_channel_ids(db, principal.user_id)
            owned_projects = select(Project.id).where(
                Project.sales_owner_id == principal.user_id
            )
            owned_customers = select(TerminalCustomer.id).where(
                TerminalCustomer.customer_owner_id == principal.user_id
            )
            conditions = [
                model.project_id.in_(owned_projects),
                model.terminal_customer_id.in_(owned_customers),
            ]
            if assigned_channels:
                conditions.append(model.channel_id.in_(assigned_channels))
            return query.where(or_(*conditions))

        if principal.is_technician:
            related_project_ids = await get_technician_related_project_ids(
                db, principal.user_id
            )
            if not related_project_ids:
                return query.where(model.id.in_([]))
            return query.where(model.project_id.in_(related_project_ids))

        return query.where(model.id.in_([]))

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
    ) -> None:
        if principal.role in {"admin", "business", "finance"}:
            return None

        if principal.is_sales:
            if obj.project and getattr(obj.project, "sales_owner_id", None) == principal.user_id:
                return None
            if (
                getattr(obj, "terminal_customer", None)
                and getattr(obj.terminal_customer, "customer_owner_id", None)
                == principal.user_id
            ):
                return None
            assigned_channels = await get_assigned_channel_ids(db, principal.user_id)
            if getattr(obj, "channel_id", None) in assigned_channels:
                return None
            raise HTTPException(status_code=403, detail="无权限访问此合同")

        if principal.is_technician:
            related_project_ids = await get_technician_related_project_ids(
                db, principal.user_id
            )
            if obj.project_id in related_project_ids:
                return None
            raise HTTPException(status_code=403, detail="无权限访问此合同")

        raise HTTPException(status_code=403, detail="无权限访问此合同")

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        if principal.role in {"admin", "business", "finance"}:
            return None

        if principal.is_sales:
            from app.models.customer import TerminalCustomer
            from app.models.project import Project

            project = await db.get(Project, payload.project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            if project.sales_owner_id == principal.user_id:
                return None

            assigned_channels = await get_assigned_channel_ids(db, principal.user_id)
            target_channel_id = payload.channel_id or project.channel_id
            if target_channel_id is not None and target_channel_id in assigned_channels:
                return None

            target_customer_id = payload.terminal_customer_id or project.terminal_customer_id
            if target_customer_id is not None:
                customer = await db.get(TerminalCustomer, target_customer_id)
                if customer and customer.customer_owner_id == principal.user_id:
                    return None

            raise HTTPException(status_code=403, detail="只能修改自己负责或分配的合同")

        raise HTTPException(status_code=403, detail="无权限创建合同")
