"""
统一策略层服务入口

PolicyService 提供统一的权限判断入口，所有 router 通过此服务调用权限逻辑。
"""

from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from .types import Resource, Action, PolicyResult
from .context import PrincipalContext
from .registry import get_policy_class, is_registered
from .base import BasePolicy, DefaultPolicy


class PolicyService:
    """
    权限策略服务

    对外提供统一调用入口，所有权限判断都通过此服务进行。

    Phase 1 阶段：
    - 对于已注册的资源，调用对应 Policy
    - 对于未注册的资源，使用 DefaultPolicy（不做限制）
    - 不改变现有行为
    """

    def __init__(self):
        self._default_policy = DefaultPolicy()

    def _get_policy(self, resource: Resource) -> BasePolicy:
        """获取资源的 Policy 实例"""
        policy_class = get_policy_class(resource)
        if policy_class:
            return policy_class()
        return self._default_policy

    async def authorize(
        self,
        *,
        resource: Resource,
        action: Action,
        principal: PrincipalContext,
        db: AsyncSession,
        obj: Any,
        **kwargs: Any,
    ) -> None:
        """
        单对象权限检查

        允许时返回 None，拒绝时抛 HTTPException(403)。

        Args:
            resource: 资源名
            action: 动作类型
            principal: 当前用户上下文
            db: 数据库会话
            obj: 实体对象
        """
        policy = self._get_policy(resource)
        await policy.authorize(
            principal=principal,
            db=db,
            action=action,
            obj=obj,
            **kwargs,
        )

    async def authorize_create(
        self,
        *,
        resource: Resource,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
        **kwargs: Any,
    ) -> None:
        """
        创建前权限检查

        允许时返回 None，拒绝时抛 HTTPException(403)。

        Args:
            resource: 资源名
            principal: 当前用户上下文
            db: 数据库会话
            payload: 创建请求的数据
        """
        policy = self._get_policy(resource)
        await policy.authorize_create(
            principal=principal,
            db=db,
            payload=payload,
            **kwargs,
        )

    async def scope_query(
        self,
        *,
        resource: Resource,
        action: Action = "list",
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        **kwargs: Any,
    ) -> Any:
        """
        列表查询的数据范围过滤

        Args:
            resource: 资源名
            action: 动作类型
            principal: 当前用户上下文
            db: 数据库会话
            query: SQLAlchemy 查询对象
            model: 资源模型类

        Returns:
            过滤后的查询对象
        """
        policy = self._get_policy(resource)
        return await policy.scope_query(
            principal=principal,
            db=db,
            query=query,
            model=model,
            action=action,
            **kwargs,
        )

    async def can(
        self,
        *,
        resource: Resource,
        action: Action,
        principal: PrincipalContext,
        db: AsyncSession,
        obj: Any,
        **kwargs: Any,
    ) -> PolicyResult:
        """
        非强制权限检查（不抛异常）

        用于前端能力透出等场景。

        Args:
            resource: 资源名
            action: 动作类型
            principal: 当前用户上下文
            db: 数据库会话
            obj: 实体对象

        Returns:
            PolicyResult 包含决策结果
        """
        policy = self._get_policy(resource)
        return await policy.can(
            principal=principal,
            db=db,
            action=action,
            obj=obj,
            **kwargs,
        )

    def is_policy_registered(self, resource: Resource) -> bool:
        """检查资源是否已注册 Policy"""
        return is_registered(resource)


# 全局单例服务实例
policy_service = PolicyService()


def build_principal(user_dict: dict) -> PrincipalContext:
    """
    从 user dict 构建 PrincipalContext

    便捷函数，用于 router 中快速构建上下文。

    Args:
        user_dict: get_current_user() 返回的 dict

    Returns:
        PrincipalContext 实例
    """
    return PrincipalContext.from_dict(user_dict)
