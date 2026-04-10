#!/usr/bin/env python3
"""
Test script for dispatch integration service.
"""

import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.services.dispatch_integration_service import DispatchIntegrationService
from app.database import get_db


async def test_dispatch_service():
    """Test the dispatch integration service."""
    print("Testing dispatch integration service...")

    # Test the order type determination
    service = DispatchIntegrationService("http://localhost:3001")

    # Test lead -> CO (Company Office)
    order_type = service.determine_order_type("lead", False)
    assert order_type == "CO", f"Expected CO, got {order_type}"
    print("✓ Lead type mapping correct")

    # Test opportunity with channel -> CF (Company Field)
    order_type = service.determine_order_type("opportunity", True)
    assert order_type == "CF", f"Expected CF, got {order_type}"
    print("✓ Opportunity with channel mapping correct")

    # Test opportunity without channel -> CO (Company Office)
    order_type = service.determine_order_type("opportunity", False)
    assert order_type == "CO", f"Expected CO, got {order_type}"
    print("✓ Opportunity without channel mapping correct")

    # Test project -> CF (Company Field)
    order_type = service.determine_order_type("project", False)
    assert order_type == "CF", f"Expected CF, got {order_type}"
    print("✓ Project type mapping correct")

    await service.close()
    print("All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_dispatch_service())
