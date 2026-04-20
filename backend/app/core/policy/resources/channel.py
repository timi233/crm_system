from typing import Any
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..types import Resource
from ..context import PrincipalContext
from ..helpers import (
    has_full_access,
    get_assigned_channel_ids,
    get_technician_related_channel_ids,
)


class ChannelPolicy(BasePolicy):
    resource: Resource = "channel"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: str = "list",
    ) -> Any:
        if has_full_access(principal):
            return query

        if principal.role == "sales":
            assigned_channel_ids = await get_assigned_channel_ids(db, principal.user_id)
            if not assigned_channel_ids:
                return query.where(model.id.in_([]))
            return query.where(model.id.in_(assigned_channel_ids))

        if principal.role == "technician":
            related_channel_ids = await get_technician_related_channel_ids(
                db, principal.user_id
            )
            if not related_channel_ids:
                return query.where(model.id.in_([]))
            return query.where(model.id.in_(related_channel_ids))

        if principal.role == "finance":
            return query.where(model.id.in_([]))

        return query.where(model.id.in_([]))

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: str,
        obj: Any,
    ) -> None:
        from app.models.channel_assignment import ChannelAssignment, PermissionLevel

        if has_full_access(principal):
            return

        if principal.role == "sales":
            stmt = select(ChannelAssignment.permission_level).where(
                ChannelAssignment.user_id == principal.user_id,
                ChannelAssignment.channel_id == obj.id,
            )
            result = await db.execute(stmt)
            permission_level = result.scalar_one_or_none()

            if permission_level is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="您无权访问此渠道"
                )

            if action in ["list", "read"]:
                return
            elif action == "update":
                if permission_level in [PermissionLevel.write, PermissionLevel.admin]:
                    return
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限修改此渠道"
                )
            elif action in ["delete", "manage"]:
                if permission_level == PermissionLevel.admin:
                    return
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="您没有权限管理或删除此渠道",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限执行此操作"
                )

        if principal.role == "technician":
            related_channel_ids = await get_technician_related_channel_ids(
                db, principal.user_id
            )
            if obj.id in related_channel_ids:
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您只能访问与您工单相关的渠道",
            )

        if principal.role == "finance":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="财务人员无权访问渠道数据"
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限操作此渠道"
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
            detail="只有管理员和业务角色可以创建渠道",
        )
