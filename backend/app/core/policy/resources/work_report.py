from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ..base import BasePolicy
from ..context import PrincipalContext
from ..helpers import owner_filter
from ..types import Action


class WorkReportPolicy(BasePolicy):
    resource = "work_report"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: Action = "list",
    ) -> Any:
        if principal.role == "admin":
            return query

        if principal.role == "business":
            return query

        if principal.role in ("sales", "technician", "channel_ops"):
            return query.where(owner_filter(model, "owner_id", principal.user_id))

        return query.where(model.id.in_([]))

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
    ) -> None:
        if principal.role == "admin":
            return

        if principal.role == "business":
            return

        report_owner_id = getattr(obj, "owner_id", None)

        if principal.role in ("sales", "technician", "channel_ops"):
            if action in ("list", "read"):
                if report_owner_id == principal.user_id:
                    return

            if action == "update":
                status = getattr(obj, "status", None)
                if report_owner_id == principal.user_id and status in ("draft", "withdrawn"):
                    return

            if action == "submit":
                status = getattr(obj, "status", None)
                if report_owner_id == principal.user_id and status in ("draft", "withdrawn"):
                    return

            if action == "withdraw":
                status = getattr(obj, "status", None)
                if report_owner_id == principal.user_id and status == "submitted":
                    return

        raise HTTPException(status_code=403, detail="无权限访问此工作报告")

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        if principal.role == "admin":
            return

        if principal.role == "business":
            return

        if principal.role in ("sales", "technician", "channel_ops"):
            return

        raise HTTPException(status_code=403, detail="无权限创建工作报告")

    async def can_team_read(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
    ) -> bool:
        if principal.role == "admin":
            return True

        if principal.role == "business":
            return True

        from app.models.user import User
        result = await db.execute(
            select(User).where(User.department_manager_id == principal.user_id)
        )
        members = result.scalars().all()
        return len(members) > 0