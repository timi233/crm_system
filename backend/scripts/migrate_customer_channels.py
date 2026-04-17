#!/usr/bin/env python3
"""
Migrate existing customer.channel_id to CustomerChannelLink table.

This script reads all TerminalCustomer records with channel_id and creates
corresponding CustomerChannelLink records with role='主渠道'.
"""

import os
import sys
import asyncio
from datetime import date

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base
from app.models.customer import TerminalCustomer
from app.models.customer_channel_link import CustomerChannelLink


async def migrate_customer_channels():
    """Migrate existing customer.channel_id to CustomerChannelLink table."""
    async with AsyncSession(engine) as session:
        try:
            # Query all TerminalCustomer records with channel_id
            customers = await session.execute(
                sa.select(TerminalCustomer).where(
                    TerminalCustomer.channel_id.is_not(None)
                )
            )
            customers = customers.scalars().all()

            print(f"Found {len(customers)} customers with channel_id")

            migrated_count = 0
            for customer in customers:
                # Create CustomerChannelLink record
                link = CustomerChannelLink(
                    customer_id=customer.id,
                    channel_id=customer.channel_id,
                    role="主渠道",
                    start_date=date.today(),
                    end_date=None,
                    notes=f"Migrated from TerminalCustomer.channel_id on {date.today()}",
                )
                session.add(link)
                migrated_count += 1

                # Print progress every 100 records
                if migrated_count % 100 == 0:
                    print(f"Migrated {migrated_count} records...")

            await session.commit()
            print(f"Successfully migrated {migrated_count} customer channel links")

        except Exception as e:
            print(f"Error during migration: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    print("Starting customer channel migration...")
    asyncio.run(migrate_customer_channels())
    print("Migration completed!")
