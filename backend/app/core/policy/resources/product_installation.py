from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..types import Action, Resource


class ProductInstallationPolicy(BasePolicy):
    resource: Resource = "product_installation"

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
        if principal.role == "admin":
            return query
        if principal.role == "business":
            return query
        return query.where(model.created_by_id == principal.user_id)

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
        **kwargs: Any,
    ) -> None:
        if principal.role == "admin":
            return
        if principal.role == "business":
            return
        if obj.created_by_id == principal.user_id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此产品装机记录",
        )

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
        **kwargs: Any,
    ) -> None:
        if principal.role in ("admin", "business", "sales", "technician", "channel_ops"):
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限创建产品装机记录",
        )
