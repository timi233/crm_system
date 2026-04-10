import asyncio
from sqlalchemy import select, func
from app.database import get_db
from app.models.contract import Contract
from app.models.project import Project
from app.models.user import User
from app.models.payment_plan import PaymentPlan


async def debug_performance_report():
    async for db in get_db():
        try:
            print("=== Debug Performance Report ===")

            # Test user query
            print("1. Testing user query...")
            user_result = await db.execute(select(User))
            users = user_result.scalars().all()
            print(f"Found {len(users)} users")

            # Test contract query
            print("2. Testing contract query...")
            contract_query = (
                select(Contract, Project.sales_owner_id, User.name)
                .join(Project, Contract.project_id == Project.id)
                .join(User, Project.sales_owner_id == User.id)
                .where(Contract.contract_direction == "Downstream")
            )
            contract_result = await db.execute(contract_query)
            contract_rows = contract_result.all()
            print(f"Found {len(contract_rows)} contract rows")

            # Test payment plan query
            print("3. Testing payment plan query...")
            payment_query = (
                select(PaymentPlan, Contract, Project.sales_owner_id)
                .join(Contract, PaymentPlan.contract_id == Contract.id)
                .join(Project, Contract.project_id == Project.id)
                .where(PaymentPlan.actual_date.isnot(None))
            )
            payment_result = await db.execute(payment_query)
            payment_rows = payment_result.all()
            print(f"Found {len(payment_rows)} payment rows")

            print("=== All queries successful ===")
            await db.close()

        except Exception as e:
            print(f"Error in performance report debug: {e}")
            import traceback

            traceback.print_exc()
            await db.close()


if __name__ == "__main__":
    asyncio.run(debug_performance_report())
