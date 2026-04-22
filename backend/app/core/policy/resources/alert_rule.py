from typing import Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..base import BasePolicy
from ..types import Resource, Action
from ..context import PrincipalContext
class AlertRulePolicy(BasePolicy):
    resource: Resource = "alert_rule"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: Action = "list",
    ) -> Any:
        """列表查询的数据范围过滤"""
        if principal.role == "admin":
            return query

        # 其他角色无权限访问预警规则（系统级配置）
        return query.where(model.id.in_([]))

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
    ) -> None:
        """单对象的权限检查"""
        if principal.role == "admin":
            return

        # 其他角色直接拒绝访问
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限访问预警规则配置"
        )

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        """创建前的权限检查"""
        if principal.role == "admin":
            return

        # 仅 admin/business 可以创建预警规则
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限创建预警规则配置"
        )
