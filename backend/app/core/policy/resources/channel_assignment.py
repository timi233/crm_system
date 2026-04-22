from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..types import Action, Resource


class ChannelAssignmentPolicy(BasePolicy):
    resource: Resource = "channel_assignment"

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
        if principal.role == "admin":
            return
        raise HTTPException(status_code=403, detail="需要管理员权限")

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        if principal.role == "admin":
            return
        raise HTTPException(status_code=403, detail="需要管理员权限")
