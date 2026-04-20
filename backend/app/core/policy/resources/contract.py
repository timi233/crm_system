from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..types import Resource, Action
from ..context import PrincipalContext
from ..helpers import has_full_access, get_technician_related_project_ids
from fastapi import HTTPException


class ContractPolicy(BasePolicy):
    resource: Resource = "contract"

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

        if principal.is_sales:
            from app.models.project import Project

            return query.join(Project, model.project_id == Project.id).where(
                Project.sales_owner_id == principal.user_id
            )

        if principal.is_technician:
            related_project_ids = await get_technician_related_project_ids(
                db, principal.user_id
            )
            if not related_project_ids:
                return query.where(model.id.in_([]))
            return query.where(model.project_id.in_(related_project_ids))

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
            return None

        if principal.is_sales:
            if obj.project and obj.project.sales_owner_id == principal.user_id:
                return None
            raise HTTPException(status_code=403, detail="无权限访问此合同")

        if principal.is_technician:
            related_project_ids = await get_technician_related_project_ids(
                db, principal.user_id
            )
            if obj.project_id in related_project_ids:
                return None
            raise HTTPException(status_code=403, detail="无权限访问此合同")

        raise HTTPException(status_code=403, detail="财务角色无权访问合同")

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        if has_full_access(principal):
            return None

        if principal.is_sales:
            return None

        raise HTTPException(status_code=403, detail="无权限创建合同")
