"""
Object-level authorization checker for CRM system.

This module provides fine-grained permission checks based on entity ownership,
channel assignments, and user roles. It replaces the coarse role-based checks
in assert_can_mutate_entity with proper object-level authorization.

Design decisions:
- admin: full access (no restrictions)
- business: full access to business entities (intentional design, "准管理员")
- finance: restricted to financial entities + ownership check
- sales: ownership match OR channel assignment
- technician: work order assignment only
"""

from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional


class EntityPermissionChecker:
    """Object-level authorization checker."""

    FINANCE_ENTITIES = {"Project", "Contract", "TerminalCustomer", "PaymentPlan"}
    BUSINESS_ENTITIES = {
        "Lead",
        "Opportunity",
        "Project",
        "WorkOrder",
        "TerminalCustomer",
        "FollowUp",
        "DispatchRecord",
    }

    async def check_can_mutate(
        self, entity: Any, current_user: dict, db: AsyncSession
    ) -> None:
        """
        Check if user has permission to mutate (create/update/delete) an entity.

        Raises HTTPException with 403 if access denied.
        """
        user_role = current_user.get("role")
        user_id = current_user.get("id")

        if user_role == "admin":
            return

        entity_type = type(entity).__name__

        if user_role == "business":
            self._check_business_access(entity_type)
            return

        if user_role == "finance":
            await self._check_finance_access(entity, entity_type, user_id, db)
            return

        if user_role == "sales":
            await self._check_sales_access(entity, user_id, db)
            return

        if user_role == "technician":
            await self._check_technician_access(entity, user_id, db)
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限修改此数据"
        )

    def _check_business_access(self, entity_type: str) -> None:
        """
        Business role can mutate business entities (intentional design).
        This is a "准管理员" role with broad business data access.
        """
        if entity_type not in self.BUSINESS_ENTITIES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"商务角色无权限修改 {entity_type}",
            )

    async def _check_finance_access(
        self, entity: Any, entity_type: str, user_id: int, db: AsyncSession
    ) -> None:
        """
        Finance role can only mutate financial entities AND must be owner.
        """
        if entity_type not in self.FINANCE_ENTITIES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"财务角色无权限修改 {entity_type}",
            )

        # Finance must also be owner of the entity
        if not self._check_owner_match(entity, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能修改自己负责的财务数据",
            )

    async def _check_sales_access(
        self, entity: Any, user_id: int, db: AsyncSession
    ) -> None:
        """
        Sales role can mutate entities they own OR are assigned via channel.
        """
        # 1. Check direct ownership
        if self._check_owner_match(entity, user_id):
            return

        # 2. Check channel assignment
        if await self._check_channel_access(entity, user_id, db):
            return

        # 3. For FollowUp, check if user owns the related entity
        entity_type = type(entity).__name__
        if entity_type == "FollowUp":
            if await self._check_followup_related_access(entity, user_id, db):
                return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="只能修改自己负责或分配的数据"
        )

    async def _check_technician_access(
        self, entity: Any, user_id: int, db: AsyncSession
    ) -> None:
        """
        Technician can only modify WorkOrders they are assigned to.
        """
        from app.models.work_order import WorkOrder, WorkOrderTechnician

        entity_type = type(entity).__name__
        if entity_type != "WorkOrder":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="技术员只能修改工单"
            )

        # Check if technician is assigned to this work order
        result = await db.execute(
            select(WorkOrderTechnician).where(
                WorkOrderTechnician.work_order_id == entity.id,
                WorkOrderTechnician.technician_id == user_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="只能修改分配给自己的工单"
            )

    def _check_owner_match(self, entity: Any, user_id: int) -> bool:
        """
        Check if entity's owner field matches user ID.

        Checks: sales_owner_id, customer_owner_id, follower_id, submitter_id, related_sales_id
        """
        owner_fields = [
            "sales_owner_id",
            "customer_owner_id",
            "follower_id",
            "submitter_id",
            "related_sales_id",
        ]

        for field in owner_fields:
            if hasattr(entity, field):
                owner_value = getattr(entity, field)
                if owner_value == user_id:
                    return True

        return False

    async def _check_channel_access(
        self, entity: Any, user_id: int, db: AsyncSession
    ) -> bool:
        """
        Check if entity's channel is assigned to the current user.
        """
        from app.models.channel_assignment import ChannelAssignment

        if not hasattr(entity, "channel_id") or entity.channel_id is None:
            return False

        result = await db.execute(
            select(ChannelAssignment).where(
                ChannelAssignment.channel_id == entity.channel_id,
                ChannelAssignment.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def _check_followup_related_access(
        self, entity: Any, user_id: int, db: AsyncSession
    ) -> bool:
        """
        For FollowUp, check if user owns the related entity (lead, opportunity, project).
        """
        from app.models.lead import Lead
        from app.models.opportunity import Opportunity
        from app.models.project import Project
        from app.models.customer import TerminalCustomer

        # Check if user owns the related entity
        if entity.lead_id:
            result = await db.execute(select(Lead).where(Lead.id == entity.lead_id))
            lead = result.scalar_one_or_none()
            if lead and lead.sales_owner_id == user_id:
                return True

        if entity.opportunity_id:
            result = await db.execute(
                select(Opportunity).where(Opportunity.id == entity.opportunity_id)
            )
            opp = result.scalar_one_or_none()
            if opp and opp.sales_owner_id == user_id:
                return True

        if entity.project_id:
            result = await db.execute(
                select(Project).where(Project.id == entity.project_id)
            )
            project = result.scalar_one_or_none()
            if project and project.sales_owner_id == user_id:
                return True

        if entity.terminal_customer_id:
            result = await db.execute(
                select(TerminalCustomer).where(
                    TerminalCustomer.id == entity.terminal_customer_id
                )
            )
            customer = result.scalar_one_or_none()
            if customer and customer.customer_owner_id == user_id:
                return True

        return False


# Singleton instance for easy import
permission_checker = EntityPermissionChecker()


async def assert_can_mutate_entity_v2(
    entity: Any, current_user: dict, db: AsyncSession
) -> None:
    """
    Assert that user can mutate an entity using object-level authorization.

    This is the new version that replaces assert_can_mutate_entity in dependencies.py.
    """
    await permission_checker.check_can_mutate(entity, current_user, db)


async def assert_can_access_entity_v2(
    entity: Any, current_user: dict, db: AsyncSession
) -> None:
    """
    Assert that user can access (read) an entity using object-level authorization.

    Read permissions are generally more permissive than write permissions:
    - admin: full access (no restrictions)
    - business: full access to business entities (intentional design, "准管理员")
    - finance: access to financial entities + ownership check
    - sales: ownership match OR channel assignment
    - technician: work order assignment or related customer access
    """
    from fastapi import HTTPException, status

    user_role = current_user.get("role")
    user_id = current_user.get("id")

    if user_role == "admin":
        return

    entity_type = type(entity).__name__

    if user_role == "business":
        # Business role can access business entities (intentional design).
        if entity_type not in permission_checker.BUSINESS_ENTITIES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"商务角色无权限访问 {entity_type}",
            )
        return

    if user_role == "finance":
        # Finance role can access financial entities AND must be owner.
        if entity_type not in permission_checker.FINANCE_ENTITIES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"财务角色无权限访问 {entity_type}",
            )
        # Finance must also be owner of the entity
        if not permission_checker._check_owner_match(entity, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能访问自己负责的财务数据",
            )
        return

    if user_role == "sales":
        # Sales role can access entities they own OR are assigned via channel.
        if permission_checker._check_owner_match(
            entity, user_id
        ) or await permission_checker._check_channel_access(entity, user_id, db):
            return

        # For FollowUp, check if user owns the related entity
        if entity_type == "FollowUp":
            if await permission_checker._check_followup_related_access(
                entity, user_id, db
            ):
                return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="只能访问自己负责或分配的数据"
        )

    if user_role == "technician":
        # Technician can access WorkOrders they are assigned to, or related customers
        if entity_type == "WorkOrder":
            from app.models.work_order import WorkOrderTechnician

            result = await db.execute(
                select(WorkOrderTechnician).where(
                    WorkOrderTechnician.work_order_id == entity.id,
                    WorkOrderTechnician.technician_id == user_id,
                )
            )
            if result.scalar_one_or_none() is not None:
                return
        elif entity_type == "TerminalCustomer":
            # Technicians can access customers through their work orders
            from app.models.work_order import WorkOrder

            result = await db.execute(
                select(WorkOrder)
                .where(WorkOrder.terminal_customer_id == entity.id)
                .join(WorkOrderTechnician)
                .where(WorkOrderTechnician.technician_id == user_id)
            )
            if result.scalar_one_or_none() is not None:
                return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此数据"
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问此数据"
    )
