"""
Auto-numbering service for CRM system.
Format: PYCRM-{TYPE}-{YYYYMMDD}-{SEQ}
Example: PYCRM-CUST-20240101-001
"""

from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.auto_number import AutoNumber


ENTITY_TYPES = {
    "customer": "CUST",
    "lead": "LEAD",
    "opportunity": "OPP",
    "project": "PRJ",
    "contract": "CON",
    "channel": "CHAN",
    "work_order": "WO",
}


async def generate_code(db: AsyncSession, entity_type: str) -> str:
    """
    Generate auto-numbered code for an entity.

    Args:
        db: AsyncSession database session
        entity_type: One of 'customer', 'lead', 'opportunity', 'project', 'contract'

    Returns:
        Formatted code string like 'PYCRM-CUST-20240101-001'
    """
    prefix = ENTITY_TYPES.get(entity_type)
    if not prefix:
        raise ValueError(f"Unknown entity type: {entity_type}")

    today = date.today()

    result = await db.execute(
        select(AutoNumber).where(AutoNumber.entity_type == prefix)
    )
    record = result.scalar_one_or_none()

    if not record:
        seq = 1
        record = AutoNumber(entity_type=prefix, seq_date=today, current_seq=1)
        db.add(record)
    elif record.seq_date != today:
        seq = 1
        record.seq_date = today
        record.current_seq = 1
    else:
        seq = record.current_seq + 1
        record.current_seq = seq

    await db.flush()

    seq_str = str(seq).zfill(3) if seq <= 999 else str(seq)

    return f"PYCRM-{prefix}-{today.strftime('%Y%m%d')}-{seq_str}"
