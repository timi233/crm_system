from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.policy import build_principal, policy_service
from app.database import get_db
from app.models.work_report import WorkReport
from app.models.work_report_comment import WorkReportComment
from app.models.user import User
from app.schemas.work_report import (
    WorkReportCreate,
    WorkReportRead,
    WorkReportUpdate,
    WorkReportGenerateDraftRequest,
    WorkReportCommentCreate,
    WorkReportCommentRead,
)
from app.services.work_report_service import WorkReportService
from app.services.notification_service import NotificationService


router = APIRouter(prefix="/work-reports", tags=["work_reports"])


@router.get("/", response_model=list[WorkReportRead])
async def list_work_reports(
    report_type: Optional[str] = Query(None, pattern="^(daily|weekly)$"),
    owner_id: Optional[int] = Query(None, gt=0),
    status: Optional[str] = Query(None, pattern="^(draft|submitted|withdrawn)$"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    query = select(WorkReport)

    if report_type:
        query = query.where(WorkReport.report_type == report_type)
    if owner_id:
        query = query.where(WorkReport.owner_id == owner_id)
    if status:
        query = query.where(WorkReport.status == status)
    if date_from:
        query = query.where(WorkReport.report_date >= date_from)
    if date_to:
        query = query.where(WorkReport.report_date <= date_to)

    query = query.order_by(WorkReport.report_date.desc()).offset(skip).limit(limit)

    query = await policy_service.scope_query(
        resource="work_report",
        action="list",
        principal=principal,
        db=db,
        query=query,
        model=WorkReport,
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=WorkReportRead)
async def create_work_report(
    report: WorkReportCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize_create(
        resource="work_report",
        principal=principal,
        db=db,
        payload=report,
    )

    if principal.role == "finance":
        raise HTTPException(status_code=403, detail="财务角色不能创建工作报告")

    user_result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    service = WorkReportService(db)
    new_report = await service.create_or_get_report(
        owner_id=current_user["id"],
        owner_role=user.role,
        report_type=report.report_type,
        report_date=report.report_date,
    )

    if report.remark:
        new_report.remark = report.remark
        await db.commit()
        await db.refresh(new_report)

    return new_report


@router.post("/generate-draft", response_model=WorkReportRead)
async def generate_draft(
    request: WorkReportGenerateDraftRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)
    await policy_service.authorize_create(
        resource="work_report",
        principal=principal,
        db=db,
        payload=request,
    )

    if principal.role == "finance":
        raise HTTPException(status_code=403, detail="财务角色不能创建工作报告")

    user_result = await db.execute(select(User).where(User.id == current_user["id"]))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    service = WorkReportService(db)
    new_report = await service.create_or_get_report(
        owner_id=current_user["id"],
        owner_role=user.role,
        report_type=request.report_type,
        report_date=request.report_date,
    )

    return new_report


@router.get("/team", response_model=list[WorkReportRead])
async def list_team_reports(
    report_type: Optional[str] = Query(None, pattern="^(daily|weekly)$"),
    status: Optional[str] = Query(None, pattern="^(draft|submitted|withdrawn)$"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    principal = build_principal(current_user)

    can_team_read = principal.role in {"admin", "business"}
    if not can_team_read:
        member_result = await db.execute(
            select(User.id).where(User.department_manager_id == principal.user_id).limit(1)
        )
        can_team_read = member_result.scalar_one_or_none() is not None

    if not can_team_read:
        raise HTTPException(status_code=403, detail="无权限查看团队工作报告")

    service = WorkReportService(db)
    return await service.get_team_reports(
        manager_id=current_user["id"],
        full_access=principal.role in {"admin", "business"},
        report_type=report_type,
        status=status,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )


@router.get("/{report_id}", response_model=WorkReportRead)
async def get_work_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkReport).where(WorkReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="工作报告不存在")

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="work_report",
        action="read",
        principal=principal,
        db=db,
        obj=report,
    )

    return report


@router.put("/{report_id}", response_model=WorkReportRead)
async def update_work_report(
    report_id: int,
    report_update: WorkReportUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkReport).where(WorkReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="工作报告不存在")

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="work_report",
        action="update",
        principal=principal,
        db=db,
        obj=report,
    )

    if report.status not in ("draft", "withdrawn"):
        raise HTTPException(status_code=400, detail="只能编辑草稿或已撤回的报告")

    service = WorkReportService(db)
    return await service.update_report(
        report,
        remark=report_update.remark,
    )


@router.post("/{report_id}/submit", response_model=WorkReportRead)
async def submit_work_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkReport).where(WorkReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="工作报告不存在")

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="work_report",
        action="submit",
        principal=principal,
        db=db,
        obj=report,
    )

    service = WorkReportService(db)
    return await service.submit_report(report)


@router.post("/{report_id}/withdraw", response_model=WorkReportRead)
async def withdraw_work_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkReport).where(WorkReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="工作报告不存在")

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="work_report",
        action="withdraw",
        principal=principal,
        db=db,
        obj=report,
    )

    service = WorkReportService(db)
    return await service.withdraw_report(report)


@router.post("/{report_id}/regenerate", response_model=WorkReportRead)
async def regenerate_snapshot(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkReport).where(WorkReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="工作报告不存在")

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="work_report",
        action="update",
        principal=principal,
        db=db,
        obj=report,
    )

    if report.status not in ("draft", "withdrawn"):
        raise HTTPException(status_code=400, detail="只能在草稿或撤回状态重新生成")

    service = WorkReportService(db)
    return await service.regenerate_snapshot(report)


@router.get("/{report_id}/comments", response_model=list[WorkReportCommentRead])
async def list_comments(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkReport).where(WorkReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="工作报告不存在")

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="work_report",
        action="read",
        principal=principal,
        db=db,
        obj=report,
    )

    result = await db.execute(
        select(WorkReportComment, User.name)
        .join(User, WorkReportComment.user_id == User.id)
        .where(WorkReportComment.report_id == report_id)
        .order_by(WorkReportComment.created_at.asc())
    )
    rows = result.all()
    return [
        WorkReportCommentRead(
            id=row[0].id,
            report_id=row[0].report_id,
            user_id=row[0].user_id,
            user_name=row[1],
            content=row[0].content,
            created_at=row[0].created_at,
        )
        for row in rows
    ]


@router.post("/{report_id}/comments", response_model=WorkReportCommentRead, status_code=201)
async def create_comment(
    report_id: int,
    comment: WorkReportCommentCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkReport).where(WorkReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="工作报告不存在")

    principal = build_principal(current_user)
    await policy_service.authorize(
        resource="work_report",
        action="read",
        principal=principal,
        db=db,
        obj=report,
    )

    user_id = current_user["id"]

    user_result = await db.execute(select(User).where(User.id == user_id))
    commenter = user_result.scalar_one_or_none()
    commenter_name = commenter.name if commenter else ""

    new_comment = WorkReportComment(
        report_id=report_id,
        user_id=user_id,
        content=comment.content,
    )
    db.add(new_comment)

    if user_id != report.owner_id:
        notification_service = NotificationService(db)
        await notification_service.create(
            user_id=report.owner_id,
            notification_type="work_report_comment",
            title=f"你的日报/周报收到新评论",
            content=f"{commenter_name} 对你的{report.report_type == 'daily' and '日报' or '周报'}发表了评论",
            entity_type="work_report",
            entity_id=report_id,
        )

    await db.commit()
    await db.refresh(new_comment)

    return WorkReportCommentRead(
        id=new_comment.id,
        report_id=new_comment.report_id,
        user_id=new_comment.user_id,
        user_name=commenter_name,
        content=new_comment.content,
        created_at=new_comment.created_at,
    )
