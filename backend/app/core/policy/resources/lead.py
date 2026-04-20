from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..helpers import (
    get_technician_related_lead_ids,
    has_full_access,
    owner_filter,
)
from ..types import Action


class LeadPolicy(BasePolicy):
    resource = "lead"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: Action = "list",
    ) -> Any:
        if has_full_access(principal):
            return query

        if principal.role == "sales":
            return query.where(owner_filter(model, "sales_owner_id", principal.user_id))

        if principal.role == "technician":
            related_lead_ids = await get_technician_related_lead_ids(
                db, principal.user_id
            )
            if not related_lead_ids:
                return query.where(model.id.in_([]))
            return query.where(model.id.in_(related_lead_ids))

        if principal.role == "finance":
            return query.where(model.id.in_([]))

        return query.where(model.id.in_([]))

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
    ) -> None:
        if has_full_access(principal):
            return

        if principal.role == "sales":
            if getattr(obj, "sales_owner_id", None) != principal.user_id:
                raise HTTPException(status_code=403, detail="无权限访问此线索")
            return

        if principal.role == "technician":
            related_lead_ids = await get_technician_related_lead_ids(
                db, principal.user_id
            )
            if obj.id not in related_lead_ids:
                raise HTTPException(status_code=403, detail="无权限访问此线索")
            return

        if principal.role == "finance":
            raise HTTPException(status_code=403, detail="无权限访问此线索")

        raise HTTPException(status_code=403, detail="无权限访问此线索")

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        if has_full_access(principal):
            return

        if principal.role == "sales":
            payload_owner_id = (
                payload.sales_owner_id
                if hasattr(payload, "sales_owner_id")
                else payload.get("sales_owner_id")
            )
            if payload_owner_id != principal.user_id:
                raise HTTPException(status_code=403, detail="只能创建自己负责的线索")
            return

        raise HTTPException(status_code=403, detail="无权限创建此线索")
