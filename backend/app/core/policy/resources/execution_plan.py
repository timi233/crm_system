"""
执行计划资源权限策略

实现执行计划资源的细粒度权限控制：
- admin/business: 全量访问（读/写）
- sales:
  - 读：可以访问自己关联的（user_id == self）或自己被分配渠道的执行计划
  - 写：仅能创建自己负责的（user_id == self）
- technician/finance: 无权限
"""

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..types import Resource, Action
from ..context import PrincipalContext
from ..helpers import has_full_access, get_assigned_channel_ids
from fastapi import HTTPException


class ExecutionPlanPolicy(BasePolicy):
    """执行计划资源权限策略"""

    resource: Resource = "execution_plan"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: Action = "list",
    ) -> Any:
        """
        列表查询的数据范围过滤

        Args:
            principal: 当前用户上下文
            db: 数据库会话
            query: SQLAlchemy 查询对象
            model: 资源模型类
            action: 动作类型

        Returns:
            过滤后的查询对象
        """
        # admin/business: 不过滤
        if has_full_access(principal):
            return query

        # sales: 可以访问自己关联的或自己被分配渠道的执行计划
        if principal.is_sales:
            # 1. user_id == principal.user_id
            # 2. channel_id in (assigned channel ids)
            from app.models.channel_assignment import ChannelAssignment

            assigned_channel_ids = await get_assigned_channel_ids(db, principal.user_id)

            if not assigned_channel_ids:
                # 没有分配的渠道，只能访问自己创建的
                return query.where(model.user_id == principal.user_id)

            # 自己创建的 OR 所属渠道被自己分配的
            return query.where(
                (model.user_id == principal.user_id)
                | (model.channel_id.in_(assigned_channel_ids))
            )

        # technician: 无权限
        if principal.is_technician:
            return query.where(model.id.in_([]))

        # finance: 无权限
        if principal.is_finance:
            return query.where(model.id.in_([]))

        # 默认拒绝
        return query.where(model.id.in_([]))

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
    ) -> None:
        """
        单对象的权限检查

        允许时返回 None，拒绝时抛 HTTPException(403)。

        Args:
            principal: 当前用户上下文
            db: 数据库会话
            action: 动作类型
            obj: 实体对象
        """
        # admin/business: 允许
        if has_full_access(principal):
            return None

        # sales: 必须匹配 user_id 或 channel 在分配列表中
        if principal.is_sales:
            if action == "read":
                if obj.user_id == principal.user_id:
                    return None

                assigned_channel_ids = await get_assigned_channel_ids(
                    db, principal.user_id
                )
                if obj.channel_id in assigned_channel_ids:
                    return None
            else:
                if obj.user_id == principal.user_id:
                    return None

                writable_channel_ids = await get_assigned_channel_ids(
                    db, principal.user_id, min_level="write"
                )
                if obj.channel_id in writable_channel_ids:
                    return None

            raise HTTPException(status_code=403, detail="无权限访问此执行计划")

        # technician: 直接403
        if principal.is_technician:
            raise HTTPException(status_code=403, detail="技术员无权访问执行计划")

        # finance: 直接403
        if principal.is_finance:
            raise HTTPException(status_code=403, detail="财务角色无权访问执行计划")

        # 默认拒绝
        raise HTTPException(status_code=403, detail="无权限访问此执行计划")

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        """
        创建前的权限检查

        允许时返回 None，拒绝时抛 HTTPException(403)。

        Args:
            principal: 当前用户上下文
            db: 数据库会话
            payload: 创建请求的数据
        """
        # 仅 admin/business
        if has_full_access(principal):
            return None

        # technician 和 finance 无创建权限
        if principal.is_technician or principal.is_finance:
            raise HTTPException(status_code=403, detail="无权限创建执行计划")

        if principal.is_sales:
            payload_user_id = (
                payload.user_id
                if hasattr(payload, "user_id")
                else payload.get("user_id")
            )
            payload_channel_id = (
                payload.channel_id
                if hasattr(payload, "channel_id")
                else payload.get("channel_id")
            )

            if payload_user_id != principal.user_id:
                raise HTTPException(status_code=403, detail="只能创建自己负责的培训计划")

            writable_channel_ids = await get_assigned_channel_ids(
                db, principal.user_id, min_level="write"
            )
            if payload_channel_id not in writable_channel_ids:
                raise HTTPException(status_code=403, detail="无权限为该渠道创建培训计划")

            return None

        # 默认拒绝
        raise HTTPException(status_code=403, detail="无权限创建执行计划")
