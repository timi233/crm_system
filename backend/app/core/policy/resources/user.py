from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from ..base import BasePolicy
from ..context import PrincipalContext
from ..helpers import has_full_access, has_read_only_full_access
from ..types import Action


class UserPolicy(BasePolicy):
    resource = "user"

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

        根据设计文档 docs/unified-permission-strategy-plan.md 第9.7节：
        - admin: 全量读写删
        - business/finance: 活跃用户目录只读
        - sales: 默认仅自己；如筛选 functional_role=TECHNICIAN，允许读技术员候选
        - technician: 仅自己只读
        """
        if has_full_access(principal):
            return query

        if has_read_only_full_access(principal) or principal.role == "business":
            return query.where(model.is_active == True)

        if principal.role == "sales":
            return query.where(model.id == principal.user_id)

        if principal.role == "technician":
            return query.where(model.id == principal.user_id)

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

        根据设计文档 docs/unified-permission-strategy-plan.md 第9.7节：
        - admin: 允许所有
        - business/finance: 只允许 list/read，其他403
        - sales: obj.id == principal.user_id 或 (action==read 且 obj.functional_role=="TECHNICIAN") 否则403
        - technician: obj.id == principal.user_id 且 action in [list,read] 否则403
        """
        if has_full_access(principal):
            return

        if principal.role in ("business", "finance"):
            if action in ("list", "read"):
                if not getattr(obj, "is_active", False):
                    raise HTTPException(status_code=403, detail="无权访问非活跃用户")
                return
            else:
                raise HTTPException(status_code=403, detail="无权执行此操作")

        if principal.role == "sales":
            if obj.id == principal.user_id:
                return

            if (
                action == "read"
                and getattr(obj, "functional_role", None) == "TECHNICIAN"
            ):
                return

            raise HTTPException(status_code=403, detail="无权访问此用户")

        if principal.role == "technician":
            if obj.id != principal.user_id:
                raise HTTPException(status_code=403, detail="无权访问其他用户")

            if action in ("list", "read"):
                return
            else:
                raise HTTPException(status_code=403, detail="无权执行此操作")

        raise HTTPException(status_code=403, detail="无权访问用户")

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        """
        创建前的权限检查

        根据设计文档：仅 admin 可创建
        """
        if has_full_access(principal):
            return

        raise HTTPException(status_code=403, detail="无权创建用户")
