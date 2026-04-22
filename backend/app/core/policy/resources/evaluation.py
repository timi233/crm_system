from typing import Any, cast
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from ..base import BasePolicy
from ..context import PrincipalContext
from ..helpers import has_full_access
from ..types import Action


class EvaluationPolicy(BasePolicy):
    resource = "evaluation"

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

        if principal.role == "technician":
            return query.where(model.id.in_([]))

        if principal.role == "sales":
            from app.models.evaluation import Evaluation
            from app.models.work_order import WorkOrder

            return query.join(
                WorkOrder, Evaluation.work_order_id == WorkOrder.id
            ).where(
                or_(
                    WorkOrder.submitter_id == principal.user_id,
                    WorkOrder.related_sales_id == principal.user_id,
                )
            )

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

        if principal.role == "technician":
            raise HTTPException(status_code=403, detail="无权访问评价")

        if principal.role == "sales":
            from app.models.work_order import WorkOrder

            stmt = select(WorkOrder).where(WorkOrder.id == obj.work_order_id)
            result = await db.execute(stmt)
            work_order = result.scalar_one_or_none()

            if work_order is not None:
                submitter_id = cast(int, getattr(work_order, "submitter_id", None))
                related_sales_id = cast(
                    int, getattr(work_order, "related_sales_id", None)
                )
                if (
                    submitter_id == principal.user_id
                    or related_sales_id == principal.user_id
                ):
                    return
            raise HTTPException(status_code=403, detail="无权访问此评价")

        raise HTTPException(status_code=403, detail="无权访问评价")

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
            raise HTTPException(status_code=403, detail="无权创建评价")

        if principal.role == "sales":
            work_order_id = (
                payload.work_order_id
                if hasattr(payload, "work_order_id")
                else payload.get("work_order_id")
            )
            from app.models.work_order import WorkOrder

            stmt = select(WorkOrder).where(WorkOrder.id == work_order_id)
            result = await db.execute(stmt)
            work_order = result.scalar_one_or_none()

            if work_order is not None:
                submitter_id = cast(int, getattr(work_order, "submitter_id", None))
                related_sales_id = cast(
                    int, getattr(work_order, "related_sales_id", None)
                )
                if (
                    submitter_id == principal.user_id
                    or related_sales_id == principal.user_id
                ):
                    return
            raise HTTPException(
                status_code=403, detail="只能为自己提交或负责的工单创建评价"
            )

        raise HTTPException(status_code=403, detail="无权创建评价")
