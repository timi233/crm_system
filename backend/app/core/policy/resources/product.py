from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..types import Resource
from ..context import PrincipalContext
from ..helpers import has_full_access


class ProductPolicy(BasePolicy):
    resource: Resource = "product"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: str = "list",
    ) -> Any:
        return query

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: str,
        obj: Any,
    ) -> None:
        if has_full_access(principal):
            return

        if action in ["list", "read"]:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您没有权限执行此操作",
        )

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        if has_full_access(principal):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员和业务角色可以创建产品",
        )
