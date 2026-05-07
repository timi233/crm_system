from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..types import Action, Resource


class DashboardPolicy(BasePolicy):
    resource: Resource = "dashboard"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: Action = "list",
        **kwargs: Any,
    ) -> Any:
        return query

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
        **kwargs: Any,
    ) -> None:
        if action == "manage" and principal.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限",
            )
        if action in ("read", "list"):
            if principal.role not in ("admin", "business", "sales", "finance", "technician"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限访问仪表盘",
                )
            return

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
        **kwargs: Any,
    ) -> None:
        return
