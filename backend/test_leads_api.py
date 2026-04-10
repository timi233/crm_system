import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.lead import Lead


async def test_leads_api():
    async for db in get_db():
        try:
            result = await db.execute(
                select(Lead).options(
                    selectinload(Lead.terminal_customer), selectinload(Lead.sales_owner)
                )
            )
            leads = result.scalars().all()
            print(f"Found {len(leads)} leads")

            # Try to serialize
            lead_list = []
            for l in leads:
                lead_dict = {
                    "id": l.id,
                    "lead_code": l.lead_code,
                    "lead_name": l.lead_name,
                    "terminal_customer_id": l.terminal_customer_id,
                    "lead_stage": l.lead_stage,
                    "sales_owner_id": l.sales_owner_id,
                    "created_at": str(l.created_at) if l.created_at else None,
                    "terminal_customer_name": l.terminal_customer.customer_name
                    if l.terminal_customer
                    else None,
                    "sales_owner_name": l.sales_owner.name if l.sales_owner else None,
                }
                lead_list.append(lead_dict)
                print(f"Serialized lead: {lead_dict}")

            await db.close()
            return lead_list

        except Exception as e:
            print(f"Error in API simulation: {e}")
            import traceback

            traceback.print_exc()
            await db.close()
            return []


if __name__ == "__main__":
    asyncio.run(test_leads_api())
