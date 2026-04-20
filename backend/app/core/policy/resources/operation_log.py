from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..types import Resource, Action
from ..context import PrincipalContext
from ..helpers import (
    has_full_access,
    has_read_only_full_access,
)


class OperationLogPolicy(BasePolicy):
    resource: Resource = "operation_log"

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

        if has_read_only_full_access(principal):
            return query

        return query.where(model.user_id == principal.user_id)

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
    ) -> None:
        if action in ["list", "read"]:
            if has_full_access(principal) or has_read_only_full_access(principal):
                return

            if obj.user_id == principal.user_id:
                return

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您只能查看自己的操作日志",
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="操作日志不允许修改",
        )

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="操作日志由系统自动生成，不允许手动创建",
        )
