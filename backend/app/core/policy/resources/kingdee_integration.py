from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..types import Action, Resource


class KingdeeIntegrationPolicy(BasePolicy):
    resource: Resource = "kingdee_integration"

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
        operation = kwargs.get("operation")

        if operation == "project_summary":
            if principal.role in {"admin", "finance", "business"}:
                return
        elif operation in {"projects_for_integration", "validate_project_codes"}:
            if principal.role in {"admin", "finance"}:
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
            detail="kingdee integration does not support create",
        )
