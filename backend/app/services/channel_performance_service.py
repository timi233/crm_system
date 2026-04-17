from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Contract, Opportunity, Project, UnifiedTarget


async def refresh_channel_performance(db: AsyncSession, channel_id: int):
    contract_stmt = select(func.coalesce(func.sum(Contract.contract_amount), 0)).where(
        Contract.channel_id == channel_id,
        Contract.contract_direction == "Downstream",
        Contract.contract_status == "signed",
    )
    contract_result = await db.execute(contract_stmt)
    achieved_performance = contract_result.scalar()

    opportunity_stmt = select(
        func.coalesce(func.sum(Opportunity.expected_contract_amount), 0)
    ).where(
        Opportunity.channel_id == channel_id,
        Opportunity.opportunity_stage.in_(
            ["报价投标", "合同签订", "已成交", "Won→Project"]
        ),
    )
    opportunity_result = await db.execute(opportunity_stmt)
    achieved_opportunity = opportunity_result.scalar()

    project_stmt = select(func.count(Project.id)).where(
        Project.channel_id == channel_id
    )
    project_result = await db.execute(project_stmt)
    achieved_project_count = project_result.scalar()

    update_stmt = (
        UnifiedTarget.__table__.update()
        .where(
            UnifiedTarget.channel_id == channel_id,
            UnifiedTarget.target_type == "channel",
        )
        .values(
            achieved_performance=achieved_performance,
            achieved_opportunity=achieved_opportunity,
            achieved_project_count=achieved_project_count,
        )
    )
    await db.execute(update_stmt)
    await db.commit()
