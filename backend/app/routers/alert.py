from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.alert_rule import AlertRule
from app.schemas.alert import (
    AlertItem,
    AlertRuleCreate,
    AlertRuleRead,
    AlertRuleUpdate,
    AlertSummary,
)
from app.services.alert_service import AlertService


router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=List[AlertItem])
async def get_alerts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"
    return await AlertService.calculate_alerts(db, user_id, is_admin)


@router.get("/alerts/summary", response_model=AlertSummary)
async def get_alert_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["id"]
    is_admin = current_user["role"] == "admin"
    return await AlertService.get_alert_summary(db, user_id, is_admin)


@router.get("/alert-rules", response_model=List[AlertRuleRead])
async def get_alert_rules(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return await AlertService.get_alert_rules(db, active_only=False)


@router.post("/alert-rules", response_model=AlertRuleRead)
async def create_alert_rule(
    rule: AlertRuleCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(
        select(AlertRule).where(AlertRule.rule_code == rule.rule_code)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="规则编码已存在")

    new_rule = AlertRule(
        rule_code=rule.rule_code,
        rule_name=rule.rule_name,
        rule_type=rule.rule_type,
        entity_type=rule.entity_type,
        priority=rule.priority,
        threshold_days=rule.threshold_days,
        threshold_amount=rule.threshold_amount,
        description=rule.description,
        is_active=rule.is_active,
        created_at=date.today(),
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)
    return new_rule


@router.put("/alert-rules/{rule_id}", response_model=AlertRuleRead)
async def update_alert_rule(
    rule_id: int,
    rule: AlertRuleUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    db_rule = existing.scalars().first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    db_rule.rule_name = rule.rule_name
    db_rule.rule_type = rule.rule_type
    db_rule.entity_type = rule.entity_type
    db_rule.priority = rule.priority
    db_rule.threshold_days = rule.threshold_days
    db_rule.threshold_amount = rule.threshold_amount
    db_rule.description = rule.description
    db_rule.is_active = rule.is_active
    db_rule.updated_at = str(date.today())

    await db.commit()
    await db.refresh(db_rule)
    return db_rule


@router.delete("/alert-rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    existing = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    db_rule = existing.scalars().first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    await db.delete(db_rule)
    await db.commit()
    return {"success": True}
