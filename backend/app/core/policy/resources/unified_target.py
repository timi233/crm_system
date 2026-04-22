from typing import Any
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..helpers import (
    has_full_access,
    owner_filter,
    get_assigned_channel_ids,
)
from ..types import Action


class UnifiedTargetPolicy(BasePolicy):
    resource = "unified_target"

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

        if principal.role == "sales":
            # Sales can see targets where they are owner OR assigned to the channel
            # owner_filter for user_id
            user_filter = owner_filter(model, "user_id", principal.user_id)

            # Get channels assigned to this user
            assigned_channel_ids = await get_assigned_channel_ids(db, principal.user_id)
            if assigned_channel_ids:
                channel_filter = model.channel_id.in_(assigned_channel_ids)
                return query.where(user_filter | channel_filter)
            else:
                # No channel assignments, only return user's own targets
                return query.where(user_filter)

        if principal.role == "technician":
            # Technicians have no access to unified targets
            return query.where(model.id.in_([]))

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

        if principal.role == "sales":
            # Sales can access if they own the target OR are assigned to the channel
            if action == "read":
                if getattr(obj, "user_id", None) == principal.user_id:
                    return

                if getattr(obj, "channel_id", None):
                    assigned_channel_ids = await get_assigned_channel_ids(
                        db, principal.user_id
                    )
                    if obj.channel_id in assigned_channel_ids:
                        return
            else:
                if getattr(obj, "user_id", None) == principal.user_id:
                    return

                if getattr(obj, "channel_id", None):
                    writable_channel_ids = await get_assigned_channel_ids(
                        db, principal.user_id, min_level="write"
                    )
                    if obj.channel_id in writable_channel_ids:
                        return

            raise HTTPException(status_code=403, detail="无权限访问此目标")

        if principal.role == "technician":
            raise HTTPException(status_code=403, detail="无权限访问目标数据")

        raise HTTPException(status_code=403, detail="无权限访问目标数据")

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
            payload_target_type = (
                payload.target_type
                if hasattr(payload, "target_type")
                else payload.get("target_type")
            )
            payload_channel_id = (
                payload.channel_id
                if hasattr(payload, "channel_id")
                else payload.get("channel_id")
            )
            payload_user_id = (
                payload.user_id
                if hasattr(payload, "user_id")
                else payload.get("user_id")
            )

            payload_target_type_value = (
                payload_target_type.value
                if hasattr(payload_target_type, "value")
                else payload_target_type
            )

            if payload_target_type_value == "channel":
                if not payload_channel_id:
                    raise HTTPException(status_code=403, detail="渠道目标必须指定渠道")
                writable_channel_ids = await get_assigned_channel_ids(
                    db, principal.user_id, min_level="write"
                )
                if payload_channel_id not in writable_channel_ids:
                    raise HTTPException(status_code=403, detail="无权限为该渠道分配业绩目标")
                return

            if payload_user_id != principal.user_id:
                raise HTTPException(status_code=403, detail="只能创建自己负责的目标")
            return

        raise HTTPException(status_code=403, detail="无权限创建此目标")
