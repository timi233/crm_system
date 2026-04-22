from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import BasePolicy
from ..context import PrincipalContext
from ..types import Action, Resource


class DispatchRecordPolicy(BasePolicy):
    resource: Resource = "dispatch_record"

    async def scope_query(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        query: Any,
        model: Any,
        action: Action = "list",
        **kwargs: Any,
    ) -> Any:
        if principal.role == "admin":
            return query

        return query.where(model.id.in_([]))

    async def authorize(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        action: Action,
        obj: Any,
        **kwargs: Any,
    ) -> None:
        if action in ("list", "manage", "update", "delete"):
            if principal.role == "admin":
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin can list all dispatch records",
            )

        if principal.role == "admin":
            return

        from app.models.lead import Lead
        from app.models.opportunity import Opportunity
        from app.models.project import Project
        from .lead import LeadPolicy
        from .opportunity import OpportunityPolicy
        from .project import ProjectPolicy

        if obj.source_type == "lead" and obj.lead_id:
            source = await db.get(Lead, obj.lead_id)
            if not source:
                raise HTTPException(status_code=404, detail="Lead not found")
            await LeadPolicy().authorize(
                principal=principal,
                db=db,
                action="read",
                obj=source,
            )
            return

        if obj.source_type == "opportunity" and obj.opportunity_id:
            source = await db.get(Opportunity, obj.opportunity_id)
            if not source:
                raise HTTPException(status_code=404, detail="Opportunity not found")
            await OpportunityPolicy().authorize(
                principal=principal,
                db=db,
                action="read",
                obj=source,
            )
            return

        if obj.source_type == "project" and obj.project_id:
            source = await db.get(Project, obj.project_id)
            if not source:
                raise HTTPException(status_code=404, detail="Project not found")
            await ProjectPolicy().authorize(
                principal=principal,
                db=db,
                action="read",
                obj=source,
            )
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问派工记录",
        )

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
        **kwargs: Any,
    ) -> None:
        source_obj = kwargs.get("source_obj")
        source_type = kwargs.get("source_type")

        if principal.role == "admin":
            return

        if source_obj is None or source_type is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限创建派工记录",
            )

        owner_id = getattr(source_obj, "sales_owner_id", None)
        if owner_id == principal.user_id:
            return

        detail_map = {
            "lead": "只有管理员或线索负责人才能创建派工",
            "opportunity": "只有管理员或商机负责人才能创建派工",
            "project": "只有管理员或项目负责人才能创建派工",
        }
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_map.get(source_type, "无权限创建派工记录"),
        )
