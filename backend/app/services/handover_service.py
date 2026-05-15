import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, FeishuEmploymentStatus
from app.models.employee_handover_request import EmployeeHandoverRequest, HandoverRequestStatus
from app.models.employee_handover_log import EmployeeHandoverLog, HandoverLogOperation
from app.models.customer import TerminalCustomer
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.project import Project
from app.models.followup import FollowUp
from app.models.work_order import WorkOrder, WorkOrderTechnician
from app.models.channel_assignment import ChannelAssignment
from app.models.execution_plan import ExecutionPlan

logger = logging.getLogger(__name__)


TRANSFER_ENTITY_CONFIG = {
    "TerminalCustomer": {"model": TerminalCustomer, "field": "customer_owner_id"},
    "Lead": {"model": Lead, "field": "sales_owner_id"},
    "Opportunity": {"model": Opportunity, "field": "sales_owner_id"},
    "Project": {"model": Project, "field": "sales_owner_id"},
    "FollowUp": {"model": FollowUp, "field": "follower_id"},
    "WorkOrder": {"model": WorkOrder, "field": "related_sales_id"},
    "WorkOrderTechnician": {"model": WorkOrderTechnician, "field": "technician_id"},
    "ChannelAssignment": {"model": ChannelAssignment, "field": "user_id"},
    "ExecutionPlan": {"model": ExecutionPlan, "field": "user_id"},
}


class HandoverService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_handover_requests(
        self,
        user: User,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[EmployeeHandoverRequest]:
        limit = min(max(limit, 1), 100)
        skip = max(skip, 0)

        query = select(EmployeeHandoverRequest)

        if user.role == "admin":
            pass
        else:
            query = query.where(
                EmployeeHandoverRequest.team_manager_user_id == user.id
            )

        if status:
            query = query.where(EmployeeHandoverRequest.status == status)

        query = query.order_by(EmployeeHandoverRequest.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_handover_request(
        self, request_id: int, user: User
    ) -> Optional[EmployeeHandoverRequest]:
        result = await self.db.execute(
            select(EmployeeHandoverRequest).where(EmployeeHandoverRequest.id == request_id)
        )
        request = result.scalar_one_or_none()

        if not request:
            return None

        if user.role != "admin" and request.team_manager_user_id != user.id:
            return None

        return request

    async def get_assets_preview(
        self, request: EmployeeHandoverRequest
    ) -> Dict[str, Any]:
        from_user_id = request.from_user_id
        preview = {}

        for entity_type, config in TRANSFER_ENTITY_CONFIG.items():
            if not self._is_entity_in_scope(entity_type, request.scope_config):
                continue
            model = config["model"]
            field = config["field"]

            result = await self.db.execute(
                select(func.count()).where(model.__table__.c[field] == from_user_id)
            )
            count = result.scalar() or 0
            preview[entity_type] = {
                "count": count,
                "field": field,
            }

        return preview

    def _is_entity_in_scope(
        self, entity_type: str, scope_config: Optional[Dict[str, Any]]
    ) -> bool:
        if not scope_config:
            return True

        entities = scope_config.get("entities")
        if isinstance(entities, list):
            return entity_type in entities

        value = scope_config.get(entity_type)
        if isinstance(value, bool):
            return value

        return True

    def _append_handover_remark(
        self, entity: Any, from_user_name: Optional[str]
    ) -> Optional[str]:
        if not hasattr(entity, "notes"):
            return None

        remark = f"交接自{from_user_name or '离职人员'}"
        current_notes = getattr(entity, "notes", None) or ""
        if remark in current_notes:
            return None

        setattr(entity, "notes", f"{current_notes}\n{remark}".strip())
        return remark

    async def assign_handover(
        self,
        request: EmployeeHandoverRequest,
        to_user_id: int,
        scope_config: Optional[Dict[str, Any]] = None,
    ) -> EmployeeHandoverRequest:
        result = await self.db.execute(
            select(User).where(User.id == to_user_id)
        )
        to_user = result.scalar_one_or_none()

        if not to_user:
            raise ValueError("接收人不存在")

        if not to_user.is_active:
            raise ValueError("接收人已禁用")

        if to_user.feishu_employment_status not in (
            None,
            FeishuEmploymentStatus.ACTIVE,
        ):
            raise ValueError("接收人状态异常，无法接收交接")

        request.to_user_id = to_user_id
        request.scope_config = scope_config
        request.status = HandoverRequestStatus.PENDING_EXECUTION
        request.decided_at = datetime.utcnow()

        preview = await self.get_assets_preview(request)
        request.preview_summary = preview

        await self.db.commit()
        await self.db.refresh(request)

        return request

    async def execute_handover(
        self, request: EmployeeHandoverRequest
    ) -> Dict[str, Any]:
        if request.status == HandoverRequestStatus.COMPLETED:
            return {
                "success": True,
                "message": "交接已完成",
                "already_completed": True,
            }

        if request.status not in (
            HandoverRequestStatus.PENDING_EXECUTION,
            HandoverRequestStatus.FAILED,
        ):
            raise ValueError(f"交接请求状态不允许执行: {request.status}")

        if not request.to_user_id:
            raise ValueError("交接请求未分配接收人")

        from_user_id = request.from_user_id
        to_user_id = request.to_user_id
        execution_summary: Dict[str, Any] = {
            "transferred": {},
            "skipped": {},
            "errors": [],
        }

        try:
            request.status = HandoverRequestStatus.EXECUTING

            from_user_result = await self.db.execute(
                select(User).where(User.id == from_user_id)
            )
            from_user = from_user_result.scalar_one_or_none()
            from_user_name = from_user.name if from_user else None

            for entity_type, config in TRANSFER_ENTITY_CONFIG.items():
                if not self._is_entity_in_scope(entity_type, request.scope_config):
                    execution_summary["skipped"][entity_type] = "scope_disabled"
                    continue

                model = config["model"]
                field = config["field"]

                result = await self.db.execute(
                    select(model).where(model.__table__.c[field] == from_user_id)
                )
                entities = result.scalars().all()

                transferred_count = 0
                for entity in entities:
                    setattr(entity, field, to_user_id)
                    remark = self._append_handover_remark(entity, from_user_name)

                    log = EmployeeHandoverLog(
                        handover_request_id=request.id,
                        entity_type=entity_type,
                        entity_id=entity.id,
                        field_name=field,
                        from_user_id=from_user_id,
                        to_user_id=to_user_id,
                        operation=HandoverLogOperation.TRANSFER,
                        remark_appended=remark,
                    )
                    self.db.add(log)
                    transferred_count += 1

                execution_summary["transferred"][entity_type] = transferred_count

            if from_user:
                from_user.feishu_employment_status = FeishuEmploymentStatus.HANDED_OVER

            request.status = HandoverRequestStatus.COMPLETED
            request.executed_at = datetime.utcnow()
            request.execution_summary = execution_summary

            await self.db.commit()
            await self.db.refresh(request)

            return {
                "success": True,
                "message": "交接执行成功",
                "execution_summary": execution_summary,
            }

        except Exception as e:
            logger.error(f"Handover execution failed: {e}")
            await self.db.rollback()
            request.status = HandoverRequestStatus.FAILED
            request.error_message = str(e)
            await self.db.commit()
            return {
                "success": False,
                "message": f"交接执行失败: {str(e)}",
                "errors": [str(e)],
            }

    async def cancel_handover(
        self, request: EmployeeHandoverRequest, reason: Optional[str] = None
    ) -> EmployeeHandoverRequest:
        if request.status == HandoverRequestStatus.COMPLETED:
            raise ValueError("已完成的交接不能取消")

        request.status = HandoverRequestStatus.CANCELED
        if reason:
            request.error_message = reason

        await self.db.commit()
        await self.db.refresh(request)

        return request
