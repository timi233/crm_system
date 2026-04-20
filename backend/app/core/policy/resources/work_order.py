from typing import Any
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from ..base import BasePolicy
from ..context import PrincipalContext
from ..helpers import has_full_access, get_technician_work_order_ids
from ..types import Action


class WorkOrderPolicy(BasePolicy):
    resource = "work_order"

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

        if principal.role == "finance":
            return query.where(model.id.in_([]))

        if principal.role == "sales":
            return query.where(
                or_(
                    model.submitter_id == principal.user_id,
                    model.related_sales_id == principal.user_id,
                )
            )

        if principal.role == "technician":
            work_order_ids = await get_technician_work_order_ids(db, principal.user_id)
            if not work_order_ids:
                return query.where(model.id.in_([]))
            return query.where(model.id.in_(work_order_ids))

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

        if principal.role == "finance":
            raise HTTPException(status_code=403, detail="无权访问工单")

        if principal.role == "sales":
            if (
                obj.submitter_id == principal.user_id
                or obj.related_sales_id == principal.user_id
            ):
                return
            raise HTTPException(status_code=403, detail="无权访问此工单")

        if principal.role == "technician":
            work_order_ids = await get_technician_work_order_ids(db, principal.user_id)
            if obj.id in work_order_ids:
                return
            raise HTTPException(status_code=403, detail="无权访问此工单")

        raise HTTPException(status_code=403, detail="无权访问工单")

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        if has_full_access(principal):
            return

        if principal.role == "finance":
            raise HTTPException(status_code=403, detail="无权创建工作单")

        if principal.role in ["sales", "technician"]:
            payload_submitter = (
                payload.submitter_id
                if hasattr(payload, "submitter_id")
                else payload.get("submitter_id")
            )
            if payload_submitter != principal.user_id:
                raise HTTPException(
                    status_code=403, detail="只能以自己为提交人创建工作单"
                )
            return

        raise HTTPException(status_code=403, detail="无权创建工作单")
