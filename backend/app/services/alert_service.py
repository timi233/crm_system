from datetime import date, timedelta, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.contract import Contract, PaymentPlan
from app.models.followup import FollowUp
from app.models.alert_rule import AlertRule
from app.models.project import Project


class AlertService:
    @staticmethod
    async def get_alert_rules(
        db: AsyncSession, active_only: bool = True
    ) -> List[AlertRule]:
        query = select(AlertRule)
        if active_only:
            query = query.where(AlertRule.is_active == True)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_default_rules() -> List[Dict[str, Any]]:
        return [
            {
                "rule_code": "OPP_STALLED",
                "rule_name": "商机停滞预警",
                "rule_type": "预警",
                "entity_type": "opportunities",
                "priority": "high",
                "threshold_days": 14,
                "description": "商机在非成交/非流失状态停留超过指定天数",
            },
            {
                "rule_code": "PAYMENT_OVERDUE",
                "rule_name": "逾期回款预警",
                "rule_type": "预警",
                "entity_type": "contracts",
                "priority": "high",
                "threshold_days": 0,
                "description": "合同回款计划日期已过，状态未完成",
            },
            {
                "rule_code": "FOLLOWUP_PENDING",
                "rule_name": "待跟进事项",
                "rule_type": "预警",
                "entity_type": "follow-ups",
                "priority": "medium",
                "threshold_days": 0,
                "description": "跟进记录无下一步行动",
            },
            {
                "rule_code": "LEAD_STALLED",
                "rule_name": "线索久未转化",
                "rule_type": "预警",
                "entity_type": "leads",
                "priority": "medium",
                "threshold_days": 30,
                "description": "线索创建超过指定天数未转化为商机",
            },
            {
                "rule_code": "CONTRACT_EXPIRING",
                "rule_name": "合同即将到期",
                "rule_type": "预警",
                "entity_type": "contracts",
                "priority": "low",
                "threshold_days": 30,
                "description": "合同到期日期在指定天数内",
            },
        ]

    @staticmethod
    async def calculate_alerts(
        db: AsyncSession,
        user_id: int,
        is_admin: bool,
        rules: Optional[List[AlertRule]] = None,
    ) -> List[Dict[str, Any]]:
        alerts = []
        today = date.today()

        if rules is None or len(rules) == 0:
            default_rules = await AlertService.get_default_rules()
            rules_dict = {r["rule_code"]: r for r in default_rules}
        else:
            rules_dict = {r.rule_code: r for r in rules}

        stalled_rule = rules_dict.get("OPP_STALLED")
        if stalled_rule:
            threshold_days = (
                stalled_rule.threshold_days
                if hasattr(stalled_rule, "threshold_days")
                else stalled_rule.get("threshold_days", 14)
            )
            opp_query = select(Opportunity).where(
                Opportunity.opportunity_stage.notin_(["已成交", "已流失"])
            )
            if not is_admin:
                opp_query = opp_query.where(Opportunity.sales_owner_id == user_id)
            opp_result = await db.execute(opp_query)
            opps = opp_result.scalars().all()

            for opp_obj in opps:
                created_raw = opp_obj.created_at
                if created_raw is None:
                    created = today
                elif isinstance(created_raw, str):
                    created = date.fromisoformat(created_raw)
                elif isinstance(created_raw, datetime):
                    created = created_raw.date()
                elif isinstance(created_raw, date):
                    created = created_raw
                else:
                    created = today
                days_diff = (today - created).days
                if days_diff >= threshold_days:
                    alerts.append(
                        {
                            "alert_type": "商机停滞",
                            "priority": "high",
                            "title": f"商机停滞 {days_diff} 天",
                            "content": f"商机【{opp_obj.opportunity_name}】在{opp_obj.opportunity_stage}阶段停留已超过{threshold_days}天",
                            "entity_type": "opportunities",
                            "entity_id": opp_obj.id,
                            "entity_code": opp_obj.opportunity_code,
                            "entity_name": opp_obj.opportunity_name,
                            "created_at": str(today),
                        }
                    )

        overdue_rule = rules_dict.get("PAYMENT_OVERDUE")
        if overdue_rule:
            payment_query = (
                select(PaymentPlan, Contract, Project.sales_owner_id)
                .join(Contract, PaymentPlan.contract_id == Contract.id)
                .join(Project, Contract.project_id == Project.id)
                .where(
                    PaymentPlan.payment_status != "completed",
                    PaymentPlan.plan_date < today,
                )
            )
            if not is_admin:
                payment_query = payment_query.where(Project.sales_owner_id == user_id)
            payment_result = await db.execute(payment_query)
            payments = payment_result.all()

            for payment, contract, owner_id in payments:
                overdue_days = (
                    today - (payment.plan_date if payment.plan_date else today)
                ).days
                alerts.append(
                    {
                        "alert_type": "逾期回款",
                        "priority": "high",
                        "title": f"回款逾期 {overdue_days} 天",
                        "content": f"合同【{contract.contract_name}】回款计划【{payment.plan_stage}】应回款¥{payment.plan_amount:,.0f}，已逾期{overdue_days}天",
                        "entity_type": "contracts",
                        "entity_id": contract.id,
                        "entity_code": contract.contract_code,
                        "entity_name": contract.contract_name,
                        "created_at": str(today),
                    }
                )

        pending_rule = rules_dict.get("FOLLOWUP_PENDING")
        if pending_rule:
            followup_query = select(FollowUp).where(FollowUp.next_action == None)
            if not is_admin:
                followup_query = followup_query.where(FollowUp.follower_id == user_id)
            followup_result = await db.execute(followup_query)
            followups = followup_result.scalars().all()

            for fu in followups[:10]:
                alerts.append(
                    {
                        "alert_type": "待跟进",
                        "priority": "medium",
                        "title": "缺少下一步行动",
                        "content": f"跟进记录缺少下一步行动计划",
                        "entity_type": "follow-ups",
                        "entity_id": fu.id,
                        "entity_code": f"FU-{fu.id}",
                        "entity_name": fu.follow_up_content[:50]
                        if fu.follow_up_content
                        else "跟进记录",
                        "created_at": str(fu.follow_up_date)
                        if fu.follow_up_date
                        else str(today),
                    }
                )

        lead_rule = rules_dict.get("LEAD_STALLED")
        if lead_rule:
            threshold_days = (
                lead_rule.threshold_days
                if hasattr(lead_rule, "threshold_days")
                else lead_rule.get("threshold_days", 30)
            )
            lead_query = select(Lead).where(Lead.converted_to_opportunity == False)
            if not is_admin:
                lead_query = lead_query.where(Lead.sales_owner_id == user_id)
            lead_result = await db.execute(lead_query)
            leads = lead_result.scalars().all()

            for lead in leads:
                created_raw = lead.created_at
                if created_raw is None:
                    created = today
                elif isinstance(created_raw, str):
                    created = date.fromisoformat(created_raw)
                elif isinstance(created_raw, datetime):
                    created = created_raw.date()
                elif isinstance(created_raw, date):
                    created = created_raw
                else:
                    created = today
                days_diff = (today - created).days
                if days_diff >= threshold_days:
                    alerts.append(
                        {
                            "alert_type": "线索久未转化",
                            "priority": "medium",
                            "title": f"线索未转化 {days_diff} 天",
                            "content": f"线索【{lead.lead_name}】创建已{days_diff}天，尚未转化为商机",
                            "entity_type": "leads",
                            "entity_id": lead.id,
                            "entity_code": lead.lead_code,
                            "entity_name": lead.lead_name,
                            "created_at": str(today),
                        }
                    )

        expiring_rule = rules_dict.get("CONTRACT_EXPIRING")
        if expiring_rule:
            threshold_days = (
                expiring_rule.threshold_days
                if hasattr(expiring_rule, "threshold_days")
                else expiring_rule.get("threshold_days", 30)
            )
            contract_query = (
                select(Contract, Project.sales_owner_id)
                .join(Project, Contract.project_id == Project.id)
                .where(
                    Contract.expiry_date != None,
                    Contract.expiry_date <= today + timedelta(days=threshold_days),
                    Contract.expiry_date >= today,
                )
            )
            if not is_admin:
                contract_query = contract_query.where(Project.sales_owner_id == user_id)
            contract_result = await db.execute(contract_query)
            contracts = contract_result.all()

            for contract, owner_id in contracts:
                days_to_expire = (
                    (contract.expiry_date - today).days if contract.expiry_date else 0
                )
                alerts.append(
                    {
                        "alert_type": "合同即将到期",
                        "priority": "low",
                        "title": f"合同 {days_to_expire} 天后到期",
                        "content": f"合同【{contract.contract_name}】将于{contract.expiry_date}到期，剩余{days_to_expire}天",
                        "entity_type": "contracts",
                        "entity_id": contract.id,
                        "entity_code": contract.contract_code,
                        "entity_name": contract.contract_name,
                        "created_at": str(today),
                    }
                )

        alerts.sort(
            key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3)
        )
        return alerts

    @staticmethod
    async def get_alert_summary(
        db: AsyncSession, user_id: int, is_admin: bool
    ) -> Dict[str, int]:
        alerts = await AlertService.calculate_alerts(db, user_id, is_admin)
        summary = {"high": 0, "medium": 0, "low": 0, "total": len(alerts)}
        for alert in alerts:
            priority = alert.get("priority", "medium")
            if priority in summary:
                summary[priority] += 1
        return summary
