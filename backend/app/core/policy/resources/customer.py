from typing import Any
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query

from ..base import BasePolicy
from ..types import Resource, Action
from ..context import PrincipalContext
from ..helpers import (
    has_full_access,
    has_read_only_full_access,
    owner_filter,
    get_technician_related_customer_ids,
)


class CustomerPolicy(BasePolicy):
    resource: Resource = "customer"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: Action = "list",
    ) -> Any:
        if has_full_access(principal) or has_read_only_full_access(principal):
            return query

        if principal.role == "sales":
            return query.where(
                owner_filter(model, "customer_owner_id", principal.user_id)
            )

        if principal.role == "technician":
            related_customer_ids = await get_technician_related_customer_ids(
                db, principal.user_id
            )
            if not related_customer_ids:
                return query.where(model.id.in_([]))
            return query.where(model.id.in_(related_customer_ids))

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

        if has_read_only_full_access(principal):
            if action in ["list", "read"]:
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="财务人员只能查看客户信息，不能进行修改操作",
            )

        if principal.role == "sales":
            if obj.customer_owner_id == principal.user_id:
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="您只能操作自己负责的客户"
            )

        if principal.role == "technician":
            related_customer_ids = await get_technician_related_customer_ids(
                db, principal.user_id
            )
            if obj.id in related_customer_ids:
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您只能查看与您工单相关的客户信息",
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限操作此客户"
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

        if principal.role == "sales":
            if hasattr(payload, "customer_owner_id"):
                owner_id = payload.customer_owner_id
            else:
                owner_id = getattr(payload, "customer_owner_id", None) or payload.get(
                    "customer_owner_id"
                )

            if owner_id == principal.user_id:
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您只能创建自己为负责人的客户",
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限创建客户"
        )
