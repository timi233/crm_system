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

            # Try to return as Pydantic models would
            for lead in leads:
                print(f"Lead ID: {lead.id}")
                print(f"Customer: {lead.terminal_customer}")
                print(f"Owner: {lead.sales_owner}")

            await db.close()
            return leads

        except Exception as e:
            print(f"Error in API simulation: {e}")
            import traceback

            traceback.print_exc()
            await db.close()
            return []


if __name__ == "__main__":
    asyncio.run(test_leads_api())
