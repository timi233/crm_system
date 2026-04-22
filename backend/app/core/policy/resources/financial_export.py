from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..types import Action, Resource


class FinancialExportPolicy(BasePolicy):
    resource: Resource = "financial_export"

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
        export_type = kwargs.get("export_type")

        if export_type == "summary":
            if principal.role in {"admin", "finance"}:
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        if principal.role in {"admin", "finance", "business"}:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
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
            detail="financial export does not support create",
        )
