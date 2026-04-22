from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..types import Resource, Action
from ..context import PrincipalContext


class AlertPolicy(BasePolicy):
    resource: Resource = "alert"

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
        return query.where(model.id.in_([]))

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
    ) -> None:
        if action in ("list", "read"):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限执行此预警操作"
        )

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限创建预警"
        )
