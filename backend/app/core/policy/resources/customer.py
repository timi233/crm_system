from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

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
        from app.models.channel import Channel
        from .channel import ChannelPolicy

        if has_full_access(principal):
            pass
        elif principal.role == "sales":
            if hasattr(payload, "customer_owner_id"):
                owner_id = payload.customer_owner_id
            else:
                owner_id = getattr(payload, "customer_owner_id", None) or payload.get(
                    "customer_owner_id"
                )

            if owner_id != principal.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="您只能创建自己为负责人的客户",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限创建客户"
            )

        channel_id = (
            payload.channel_id
            if hasattr(payload, "channel_id")
            else getattr(payload, "channel_id", None)
        )
        if channel_id is not None:
            channel = await db.get(Channel, channel_id)
            if not channel:
                raise HTTPException(status_code=404, detail="Channel not found")
            await ChannelPolicy().authorize(
                principal=principal,
                db=db,
                action="read",
                obj=channel,
            )
