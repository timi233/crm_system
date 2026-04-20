"""
商机资源权限策略

实现商机资源的细粒度权限控制：
- admin/business: 全量访问
- sales: 只能访问自己负责的 (sales_owner_id == self)
- technician: 只能访问工单关联的商机
- finance: 无权限
"""

from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..types import Resource, Action
from ..context import PrincipalContext
from ..helpers import (
    has_full_access,
    owner_filter,
    get_technician_related_opportunity_ids,
)
from fastapi import HTTPException


class OpportunityPolicy(BasePolicy):
    """商机资源权限策略"""

    resource: Resource = "opportunity"

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

        # sales: 只能访问自己负责的 (sales_owner_id == self)
        if principal.is_sales:
            return query.where(owner_filter(model, "sales_owner_id", principal.user_id))

        # technician: 只能访问工单关联的商机
        if principal.is_technician:
            related_opportunity_ids = await get_technician_related_opportunity_ids(
                db, principal.user_id
            )
            if not related_opportunity_ids:
                # 如果没有关联的商机，返回空查询
                return query.where(model.id.in_([]))
            return query.where(model.id.in_(related_opportunity_ids))

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

        # sales: obj.sales_owner_id == principal.user_id 否则403
        if principal.is_sales:
            if obj.sales_owner_id == principal.user_id:
                return None
            raise HTTPException(status_code=403, detail="无权限访问此商机")

        # technician: obj.id in related 否则403
        if principal.is_technician:
            related_opportunity_ids = await get_technician_related_opportunity_ids(
                db, principal.user_id
            )
            if obj.id in related_opportunity_ids:
                return None
            raise HTTPException(status_code=403, detail="无权限访问此商机")

        # finance: 直接403
        if principal.is_finance:
            raise HTTPException(status_code=403, detail="财务角色无权访问商机")

        # 默认拒绝
        raise HTTPException(status_code=403, detail="无权限访问此商机")

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
        # 仅 admin/business/sales
        if has_full_access(principal):
            return None

        if principal.is_sales:
            # sales: payload.sales_owner_id == principal.user_id
            if (
                hasattr(payload, "sales_owner_id")
                and payload.sales_owner_id == principal.user_id
            ):
                return None
            raise HTTPException(status_code=403, detail="只能创建自己负责的商机")

        # technician 和 finance 无创建权限
        if principal.is_technician or principal.is_finance:
            raise HTTPException(status_code=403, detail="无权限创建商机")

        # 默认拒绝
        raise HTTPException(status_code=403, detail="无权限创建商机")
