import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.ledger_entry import LedgerEntry


async def get_wallet_ledger(
    db: AsyncSession,
    wallet_id: str,
    limit: int = 50,
    offset: int = 0
) -> list[LedgerEntry]:
    """Get paginated ledger entries for a wallet."""
    result = await db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.wallet_id == uuid.UUID(wallet_id))
        .order_by(LedgerEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()