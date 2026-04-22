from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..types import Action, Resource
from .opportunity import OpportunityPolicy


class OpportunityConversionPolicy(BasePolicy):
    resource: Resource = "opportunity_conversion"

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
        if action == "manage":
            if principal.role == "admin":
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin only",
            )

        await OpportunityPolicy().authorize(
            principal=principal,
            db=db,
            action="update" if action == "update" else "read",
            obj=obj,
        )

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
        **kwargs: Any,
    ) -> None:
        if principal.role in {"admin", "business"}:
            return

        owner_id = getattr(payload, "sales_owner_id", None)
        if principal.role == "sales" and owner_id == principal.user_id:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
