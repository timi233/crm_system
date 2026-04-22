"""
渠道权限遗留兼容模块

渠道访问控制已迁移到统一策略层的 `ChannelPolicy`。
本文件仅为兼容旧调用而保留，不应再被新 router 依赖。

权限规则：
- admin: 全量通过
- business: 按当前系统既有"准管理员"语义处理（全量访问）
- sales: 依赖 ChannelAssignment.permission_level
- technician: 只允许访问与自己工单相关联的渠道

permission_level 解释：
- read: 查看渠道与工作台
- write: 修改渠道资料
- admin: 可管理分配、目标、执行计划
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, or_, false
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.channel_assignment import ChannelAssignment, PermissionLevel
from app.models.channel import Channel
from app.models.work_order import WorkOrder, WorkOrderTechnician


# 权限级别层级映射
PERMISSION_LEVEL_HIERARCHY = {
    "read": ["read", "write", "admin"],
    "write": ["write", "admin"],
    "admin": ["admin"],
}


def get_required_levels(required: str) -> List[str]:
    """获取满足权限级别的所有级别（权限继承）"""
    return PERMISSION_LEVEL_HIERARCHY.get(required, [])


async def get_user_channel_ids(
    db: AsyncSession, user_id: int, min_level: Optional[str] = None
) -> List[int]:
    """获取用户有权限访问的渠道ID列表

    Args:
        db: 数据库会话
        user_id: 用户ID
        min_level: 最低权限级别，None 表示只要有任何权限

    Returns:
        渠道ID列表
    """
    stmt = select(ChannelAssignment.channel_id).where(
        ChannelAssignment.user_id == user_id
    )

    if min_level:
        required_levels = get_required_levels(min_level)
        stmt = stmt.where(ChannelAssignment.permission_level.in_(required_levels))

    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def get_technician_channel_ids(db: AsyncSession, user_id: int) -> List[int]:
    """获取技术员工单相关的渠道ID列表

    Args:
        db: 数据库会话
        user_id: 用户ID（技术员）

    Returns:
        渠道ID列表
    """
    # 查询技术员被分配的工单
    technician_work_orders = select(WorkOrderTechnician.work_order_id).where(
        WorkOrderTechnician.technician_id == user_id
    )

    # 从工单中提取渠道ID
    stmt = select(WorkOrder.channel_id).where(
        or_(
            WorkOrder.id.in_(technician_work_orders), WorkOrder.submitter_id == user_id
        ),
        WorkOrder.channel_id.isnot(None),
    )

    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def apply_channel_scope_filter(
    query, model, current_user: dict, db: AsyncSession
):
    user_role = current_user.get("role")
    user_id = current_user.get("id")

    if user_id is None:
        return query.where(false())

    if user_role in ["admin", "business"]:
        return query

    if user_role == "sales":
        user_channel_ids = await get_user_channel_ids(db, user_id)
        if not user_channel_ids:
            return query.where(false())
        return query.where(model.id.in_(user_channel_ids))

    if user_role == "technician":
        tech_channel_ids = await get_technician_channel_ids(db, user_id)
        if not tech_channel_ids:
            return query.where(false())
        return query.where(model.id.in_(tech_channel_ids))

    return query.where(false())


async def assert_can_access_channel(
    db: AsyncSession, current_user: dict, channel_id: int, required_level: str = "read"
) -> Optional[ChannelAssignment]:
    user_role = current_user.get("role")
    user_id = current_user.get("id")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无法识别用户身份"
        )

    if user_role in ["admin", "business"]:
        return None

    if user_role == "sales":
        required_levels = get_required_levels(required_level)

        stmt = select(ChannelAssignment).where(
            ChannelAssignment.user_id == user_id,
            ChannelAssignment.channel_id == channel_id,
            ChannelAssignment.permission_level.in_(required_levels),
        )

        result = await db.execute(stmt)
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"用户无权访问渠道 {channel_id}，需要权限级别：{required_level}",
            )

        return assignment

    if user_role == "technician":
        # 技术员只能 read，任何更高级别请求都拒绝
        if required_level != "read":
            raise HTTPException(
                status_code=403, detail="Technicians only have read access"
            )
        tech_channel_ids = await get_technician_channel_ids(db, user_id)

        if channel_id not in tech_channel_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"用户无权访问渠道 {channel_id}，该渠道与您的工单无关",
            )

        return None

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"角色 {user_role} 无权访问渠道数据",
    )


async def check_channel_exists(db: AsyncSession, channel_id: int) -> Channel:
    """检查渠道是否存在，不存在则抛出404

    Args:
        db: 数据库会话
        channel_id: 渠道ID

    Returns:
        Channel 对象

    Raises:
        HTTPException: 404 如果渠道不存在
    """
    channel = await db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"渠道 {channel_id} 不存在"
        )
    return channel


# FastAPI 依赖函数


def require_channel_permission(required_level: str = "read"):
    """渠道权限检查依赖

    用法：
        @router.get("/{channel_id}")
        async def get_channel(
            channel_id: int,
            db: AsyncSession = Depends(get_db),
            current_user: dict = Depends(get_current_user),
            _: None = Depends(require_channel_permission("read"))
        ):
            ...
    """

    async def permission_checker(
        channel_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: dict = Depends(get_current_user),
    ):
        # 先检查渠道存在
        await check_channel_exists(db, channel_id)
        # 再检查权限
        await assert_can_access_channel(db, current_user, channel_id, required_level)
        return None

    return permission_checker


def require_channel_write():
    """渠道写入权限检查依赖"""
    return require_channel_permission("write")


def require_channel_admin():
    """渠道管理权限检查依赖"""
    return require_channel_permission("admin")


def require_channel_create():
    """渠道创建权限检查依赖（只有 admin/business 可以创建）"""

    async def permission_checker(
        current_user: dict = Depends(get_current_user),
    ):
        user_role = current_user.get("role")
        if user_role not in ["admin", "business"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"角色 {user_role} 无权创建渠道",
            )
        return None

    return permission_checker


def require_channel_delete():
    """渠道删除权限检查依赖（只有 admin 可以删除）"""

    async def permission_checker(
        current_user: dict = Depends(get_current_user),
    ):
        user_role = current_user.get("role")
        if user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"只有管理员可以删除渠道"
            )
        return None

    return permission_checker
