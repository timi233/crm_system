from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..helpers import (
    has_full_access,
    owner_filter,
)
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
        if has_full_access(principal):
            return query

        if principal.role == "sales":
            return query.where(owner_filter(model, "user_id", principal.user_id))

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
            if getattr(obj, "user_id", None) != principal.user_id:
                raise HTTPException(status_code=403, detail="无权限访问此销售目标")
            return

        raise HTTPException(status_code=403, detail="无权限访问此销售目标")

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
            payload_user_id = (
                payload.user_id
                if hasattr(payload, "user_id")
                else payload.get("user_id")
            )
            if payload_user_id != principal.user_id:
                raise HTTPException(status_code=403, detail="只能创建自己的销售目标")
            return

        raise HTTPException(status_code=403, detail="无权限创建销售目标")
