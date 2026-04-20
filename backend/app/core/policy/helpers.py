"""
统一策略层通用辅助工具

提供角色判断、owner 过滤、channel 关联、technician 工单关联等通用工具函数。
避免每个 policy 重复拼 SQL。
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import BinaryExpression

from .context import PrincipalContext


def is_admin(principal: PrincipalContext) -> bool:
    return principal.role == "admin"


def is_business(principal: PrincipalContext) -> bool:
    return principal.role == "business"


def is_sales(principal: PrincipalContext) -> bool:
    return principal.role == "sales"


def is_finance(principal: PrincipalContext) -> bool:
    return principal.role == "finance"


def is_technician(principal: PrincipalContext) -> bool:
    return principal.role == "technician"


def has_full_access(principal: PrincipalContext) -> bool:
    """admin 或 business 有全量权限"""
    return principal.role in ("admin", "business")


def has_read_only_full_access(principal: PrincipalContext) -> bool:
    """finance 有只读全量权限"""
    return principal.role == "finance"


def matches_owner(obj, owner_field: str, principal: PrincipalContext) -> bool:
    """
    检查对象的 owner 字段是否匹配当前用户

    Args:
        obj: 实体对象
        owner_field: owner 字段名（如 sales_owner_id, customer_owner_id）
        principal: 当前用户上下文

    Returns:
        是否匹配
    """
    owner_id = getattr(obj, owner_field, None)
    return owner_id == principal.user_id


def owner_filter(model, owner_field: str, user_id: int) -> BinaryExpression:
    """
    创建 owner 字段过滤条件

    用于 SQLAlchemy query.where() 过滤，筛选 owner 匹配指定用户的记录。

    Args:
        model: SQLAlchemy 模型类
        owner_field: owner 字段名（如 sales_owner_id, customer_owner_id）
        user_id: 用户 ID

    Returns:
        SQLAlchemy BinaryExpression 过滤条件
    """
    column = getattr(model, owner_field)
    return column == user_id


async def get_assigned_channel_ids(
    db: AsyncSession, user_id: int, min_level: Optional[str] = None
) -> List[int]:
    """
    获取用户被分配的渠道 ID 列表

    Args:
        db: 数据库会话
        user_id: 用户 ID
        min_level: 最低权限级别（read/write/admin），None 表示只要有任何权限

    Returns:
        渠道 ID 列表
    """
    from app.models.channel_assignment import ChannelAssignment, PermissionLevel

    PERMISSION_LEVEL_HIERARCHY = {
        "read": ["read", "write", "admin"],
        "write": ["write", "admin"],
        "admin": ["admin"],
    }

    stmt = select(ChannelAssignment.channel_id).where(
        ChannelAssignment.user_id == user_id
    )

    if min_level:
        required_levels = PERMISSION_LEVEL_HIERARCHY.get(min_level, [])
        if required_levels:
            stmt = stmt.where(ChannelAssignment.permission_level.in_(required_levels))

    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def get_technician_work_order_ids(db: AsyncSession, user_id: int) -> List[int]:
    """
    获取技术员被分配的工单 ID 列表

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        工单 ID 列表
    """
    from app.models.work_order import WorkOrder, WorkOrderTechnician

    technician_stmt = select(WorkOrderTechnician.work_order_id).where(
        WorkOrderTechnician.technician_id == user_id
    )

    result = await db.execute(technician_stmt)
    return [row[0] for row in result.all()]


async def get_technician_related_customer_ids(
    db: AsyncSession, user_id: int
) -> List[int]:
    """
    获取技术员工单关联的客户 ID 列表

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        客户 ID 列表
    """
    from app.models.work_order import WorkOrder, WorkOrderTechnician
    from app.models.customer import TerminalCustomer

    work_order_ids = await get_technician_work_order_ids(db, user_id)
    if not work_order_ids:
        return []

    stmt = select(WorkOrder.customer_name_id).where(
        WorkOrder.id.in_(work_order_ids), WorkOrder.customer_name_id.isnot(None)
    )
    result = await db.execute(stmt)
    customer_ids = [row[0] for row in result.all()]

    return customer_ids


async def get_technician_related_channel_ids(
    db: AsyncSession, user_id: int
) -> List[int]:
    """
    获取技术员工单关联的渠道 ID 列表

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        渠道 ID 列表
    """
    from app.models.work_order import WorkOrder, WorkOrderTechnician

    work_order_ids = await get_technician_work_order_ids(db, user_id)
    if not work_order_ids:
        return []

    stmt = select(WorkOrder.channel_id).where(
        WorkOrder.id.in_(work_order_ids), WorkOrder.channel_id.isnot(None)
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def get_technician_related_lead_ids(db: AsyncSession, user_id: int) -> List[int]:
    """
    获取技术员工单关联的线索 ID 列表

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        线索 ID 列表
    """
    from app.models.work_order import WorkOrder, WorkOrderTechnician

    work_order_ids = await get_technician_work_order_ids(db, user_id)
    if not work_order_ids:
        return []

    stmt = select(WorkOrder.lead_id).where(
        WorkOrder.id.in_(work_order_ids), WorkOrder.lead_id.isnot(None)
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def get_technician_related_opportunity_ids(
    db: AsyncSession, user_id: int
) -> List[int]:
    """
    获取技术员工单关联的商机 ID 列表

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        商机 ID 列表
    """
    from app.models.work_order import WorkOrder, WorkOrderTechnician

    work_order_ids = await get_technician_work_order_ids(db, user_id)
    if not work_order_ids:
        return []

    stmt = select(WorkOrder.opportunity_id).where(
        WorkOrder.id.in_(work_order_ids), WorkOrder.opportunity_id.isnot(None)
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def get_technician_related_project_ids(
    db: AsyncSession, user_id: int
) -> List[int]:
    """
    获取技术员工单关联的项目 ID 列表

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        项目 ID 列表
    """
    from app.models.work_order import WorkOrder, WorkOrderTechnician

    work_order_ids = await get_technician_work_order_ids(db, user_id)
    if not work_order_ids:
        return []

    stmt = select(WorkOrder.project_id).where(
        WorkOrder.id.in_(work_order_ids), WorkOrder.project_id.isnot(None)
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]
