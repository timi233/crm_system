import asyncio
from sqlalchemy import select
from app.database import get_db
from app.models.lead import Lead


async def test_leads_query():
    async for db in get_db():
        try:
            result = await db.execute(select(Lead))
            leads = result.scalars().all()
            print(f"Found {len(leads)} leads")
            for lead in leads:
                print(f"Lead: {lead.id}, {lead.lead_name}")
            await db.close()
        except Exception as e:
            print(f"Error querying leads: {e}")
            await db.close()


if __name__ == "__main__":
    asyncio.run(test_leads_query())
