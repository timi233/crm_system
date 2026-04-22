from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..types import Action, Resource


class CustomerFinanceViewPolicy(BasePolicy):
    resource: Resource = "customer_finance_view"

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
        if principal.role in {"admin", "finance"}:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="财务视图仅限管理员和财务角色访问",
        )

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
        **kwargs: Any,
    ) -> None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="customer finance view does not support create",
        )
