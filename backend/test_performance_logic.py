import asyncio
from sqlalchemy import select
from app.database import get_db
from app.models.contract import Contract, PaymentPlan
from app.models.project import Project
from app.models.user import User


async def test_performance_report_logic():
    async for db in get_db():
        try:
            print("=== Testing Performance Report Logic ===")

            # Simulate the actual performance report logic
            user_result = await db.execute(select(User))
            users = user_result.scalars().all()
            user_stats = {
                user.id: {
                    "user_id": user.id,
                    "user_name": user.name or "未分配",
                    "contract_count": 0,
                    "contract_amount": 0.0,
                    "received_amount": 0.0,
                    "pending_amount": 0.0,
                    "gross_margin": 0.0,
                }
                for user in users
                if user.role == "admin" or user.role == "sales"
            }
            print(f"Initialized user_stats for {len(user_stats)} users")

            # Contract query
            contract_query = (
                select(Contract, Project.sales_owner_id, User.name)
                .join(Project, Contract.project_id == Project.id)
                .join(User, Project.sales_owner_id == User.id)
                .where(Contract.contract_direction == "Downstream")
            )
            contract_result = await db.execute(contract_query)
            contract_rows = contract_result.all()
            print(f"Found {len(contract_rows)} contracts")

            total_contract = 0.0
            total_received = 0.0

            for row in contract_rows:
                contract = row[0]
                owner_id = row[1]
                owner_name = row[2]

                if owner_id in user_stats:
                    user_stats[owner_id]["contract_count"] += 1
                    contract_amount = float(contract.contract_amount or 0)
                    user_stats[owner_id]["contract_amount"] += contract_amount
                    total_contract += contract_amount

            # Payment query
            payment_query = (
                select(PaymentPlan, Contract, Project.sales_owner_id)
                .join(Contract, PaymentPlan.contract_id == Contract.id)
                .join(Project, Contract.project_id == Project.id)
                .where(PaymentPlan.actual_date.isnot(None))
            )
            payment_result = await db.execute(payment_query)
            payment_rows = payment_result.all()
            print(f"Found {len(payment_rows)} payments")

            for row in payment_rows:
                payment = row[0]
                contract = row[1]
                owner_id = row[2]

                if owner_id in user_stats:
                    received_amount = float(payment.actual_amount or 0)
                    user_stats[owner_id]["received_amount"] += received_amount
                    total_received += received_amount

            # Calculate pending amounts and margins
            total_pending = 0.0
            for uid in user_stats:
                pending = (
                    user_stats[uid]["contract_amount"]
                    - user_stats[uid]["received_amount"]
                )
                user_stats[uid]["pending_amount"] = pending
                total_pending += pending

                if user_stats[uid]["contract_amount"] > 0:
                    user_stats[uid]["gross_margin"] = round(
                        user_stats[uid]["received_amount"]
                        / user_stats[uid]["contract_amount"]
                        * 100,
                        2,
                    )
                else:
                    user_stats[uid]["gross_margin"] = 0.0

            print("Performance report calculation completed successfully!")
            print(
                f"Total contract: {total_contract}, Total received: {total_received}, Total pending: {total_pending}"
            )

            await db.close()

        except Exception as e:
            print(f"Error in performance report logic: {e}")
            import traceback

            traceback.print_exc()
            await db.close()


if __name__ == "__main__":
    asyncio.run(test_performance_report_logic())
