from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_

from ..base import BasePolicy
from ..context import PrincipalContext
from ..helpers import (
    get_technician_related_lead_ids,
    get_technician_related_opportunity_ids,
    get_technician_related_project_ids,
    get_technician_related_channel_ids,
    get_assigned_channel_ids,
    has_full_access,
)
from ..types import Action


class FollowUpPolicy(BasePolicy):
    resource = "follow_up"

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
            from app.models.lead import Lead
            from app.models.opportunity import Opportunity
            from app.models.project import Project
            from app.models.customer import TerminalCustomer

            owned_leads = await db.execute(
                Lead.__table__.select()
                .where(Lead.sales_owner_id == principal.user_id)
                .with_only_columns(Lead.id)
            )
            owned_lead_ids = [row[0] for row in owned_leads.all()]

            owned_opportunities = await db.execute(
                Opportunity.__table__.select()
                .where(Opportunity.sales_owner_id == principal.user_id)
                .with_only_columns(Opportunity.id)
            )
            owned_opportunity_ids = [row[0] for row in owned_opportunities.all()]

            owned_projects = await db.execute(
                Project.__table__.select()
                .where(Project.sales_owner_id == principal.user_id)
                .with_only_columns(Project.id)
            )
            owned_project_ids = [row[0] for row in owned_projects.all()]

            owned_customers = await db.execute(
                TerminalCustomer.__table__.select()
                .where(TerminalCustomer.customer_owner_id == principal.user_id)
                .with_only_columns(TerminalCustomer.id)
            )
            owned_customer_ids = [row[0] for row in owned_customers.all()]

            assigned_channel_ids = await get_assigned_channel_ids(db, principal.user_id)

            conditions = []
            conditions.append(model.follower_id == principal.user_id)
            if owned_lead_ids:
                conditions.append(model.lead_id.in_(owned_lead_ids))
            if owned_opportunity_ids:
                conditions.append(model.opportunity_id.in_(owned_opportunity_ids))
            if owned_project_ids:
                conditions.append(model.project_id.in_(owned_project_ids))
            if owned_customer_ids:
                conditions.append(model.terminal_customer_id.in_(owned_customer_ids))
            if assigned_channel_ids:
                conditions.append(model.channel_id.in_(assigned_channel_ids))

            return query.where(or_(*conditions))

        if principal.role == "technician":
            related_lead_ids = await get_technician_related_lead_ids(
                db, principal.user_id
            )
            related_opportunity_ids = await get_technician_related_opportunity_ids(
                db, principal.user_id
            )
            related_project_ids = await get_technician_related_project_ids(
                db, principal.user_id
            )
            tech_channel_ids = await get_technician_related_channel_ids(
                db, principal.user_id
            )

            conditions = []
            if related_lead_ids:
                conditions.append(model.lead_id.in_(related_lead_ids))
            if related_opportunity_ids:
                conditions.append(model.opportunity_id.in_(related_opportunity_ids))
            if related_project_ids:
                conditions.append(model.project_id.in_(related_project_ids))
            if tech_channel_ids:
                conditions.append(model.channel_id.in_(tech_channel_ids))

            if conditions:
                return query.where(or_(*conditions))
            else:
                return query.where(model.id.in_([]))

        if principal.role == "finance":
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
            if obj.follower_id == principal.user_id:
                return

            from app.models.lead import Lead
            from app.models.opportunity import Opportunity
            from app.models.project import Project
            from app.models.customer import TerminalCustomer

            if obj.lead_id is not None:
                result = await db.execute(
                    Lead.__table__.select()
                    .where(
                        Lead.id == obj.lead_id, Lead.sales_owner_id == principal.user_id
                    )
                    .with_only_columns(Lead.id)
                )
                if result.first() is not None:
                    return

            if obj.opportunity_id is not None:
                result = await db.execute(
                    Opportunity.__table__.select()
                    .where(
                        Opportunity.id == obj.opportunity_id,
                        Opportunity.sales_owner_id == principal.user_id,
                    )
                    .with_only_columns(Opportunity.id)
                )
                if result.first() is not None:
                    return

            if obj.project_id is not None:
                result = await db.execute(
                    Project.__table__.select()
                    .where(
                        Project.id == obj.project_id,
                        Project.sales_owner_id == principal.user_id,
                    )
                    .with_only_columns(Project.id)
                )
                if result.first() is not None:
                    return

            if obj.terminal_customer_id is not None:
                result = await db.execute(
                    TerminalCustomer.__table__.select()
                    .where(
                        TerminalCustomer.id == obj.terminal_customer_id,
                        TerminalCustomer.customer_owner_id == principal.user_id,
                    )
                    .with_only_columns(TerminalCustomer.id)
                )
                if result.first() is not None:
                    return

            if obj.channel_id is not None:
                assigned_channel_ids = await get_assigned_channel_ids(
                    db, principal.user_id
                )
                if obj.channel_id in assigned_channel_ids:
                    return

            raise HTTPException(status_code=403, detail="无权限访问此跟进记录")

        if principal.role == "technician":
            related_lead_ids = await get_technician_related_lead_ids(
                db, principal.user_id
            )
            related_opportunity_ids = await get_technician_related_opportunity_ids(
                db, principal.user_id
            )
            related_project_ids = await get_technician_related_project_ids(
                db, principal.user_id
            )
            tech_channel_ids = await get_technician_related_channel_ids(
                db, principal.user_id
            )

            has_access = False
            if obj.lead_id is not None and obj.lead_id in related_lead_ids:
                has_access = True
            elif (
                obj.opportunity_id is not None
                and obj.opportunity_id in related_opportunity_ids
            ):
                has_access = True
            elif obj.project_id is not None and obj.project_id in related_project_ids:
                has_access = True
            elif obj.channel_id is not None and obj.channel_id in tech_channel_ids:
                has_access = True

            if has_access:
                return

            raise HTTPException(status_code=403, detail="无权限访问此跟进记录")

        if principal.role == "finance":
            raise HTTPException(status_code=403, detail="无权限访问跟进记录")

        raise HTTPException(status_code=403, detail="无权限访问跟进记录")

    async def authorize_create(
        self,
        *,
        principal: PrincipalContext,
        db: AsyncSession,
        payload: Any,
    ) -> None:
        if has_full_access(principal):
            return

        if principal.role == "finance":
            raise HTTPException(status_code=403, detail="无权限创建跟进记录")

        if principal.role not in ["sales", "technician"]:
            raise HTTPException(status_code=403, detail="无权限创建跟进记录")

        return
