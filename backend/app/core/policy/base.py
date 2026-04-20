"""
统一策略层 Policy 基类

定义 BasePolicy，每个资源 Policy 必须继承此基类。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query

from .types import Resource, Action, PolicyDecision, PolicyResult
from .context import PrincipalContext


class BasePolicy(ABC):
    """
    Policy 基类

    每个资源的 Policy 必须继承此基类，并实现以下方法：
    - scope_query: 列表查询的数据范围过滤
    - authorize: 单对象的权限检查
    - authorize_create: 创建前的权限检查

    Phase 1 阶段，所有方法默认返回 NOT_APPLICABLE 或允许，
    不改变现有行为。实际逻辑在 Phase 2 迁移时逐步实现。
    """

    resource: Resource

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    async def can(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
    ) -> PolicyResult:
        """
        非强制权限检查（不抛异常）

        用于前端能力透出等场景。

        Args:
            principal: 当前用户上下文
            db: 数据库会话
            action: 动作类型
            obj: 实体对象

        Returns:
            PolicyResult 包含决策结果
        """
        try:
            await self.authorize(
                principal=principal,
                db=db,
                action=action,
                obj=obj,
            )
            return PolicyResult(decision=PolicyDecision.ALLOW)
        except Exception:
            return PolicyResult(decision=PolicyDecision.DENY)


class DefaultPolicy(BasePolicy):
    """
    默认 Policy 实现

    Phase 1 阶段使用，不做任何限制，保持现有行为。
    所有方法默认允许，后续迁移时替换为具体 Policy。
    """

    resource: Resource = "user"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: Action = "list",
    ) -> Any:
        return query

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
    ) -> None:
        return None

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        return None
