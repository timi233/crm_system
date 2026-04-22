from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..helpers import owner_filter
from ..types import Action


class SalesTargetPolicy(BasePolicy):
    resource = "sales_target"

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

        return query.where(owner_filter(model, "user_id", principal.user_id))

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

        if action in ("list", "read") and getattr(obj, "user_id", None) == principal.user_id:
            return

        raise HTTPException(status_code=403, detail="无权限访问此销售目标")

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        if principal.role == "admin":
            return

        raise HTTPException(status_code=403, detail="无权限创建销售目标")
