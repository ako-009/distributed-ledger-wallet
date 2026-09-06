from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.ledger_service import get_wallet_ledger
from app.services.wallet_service import get_wallet_by_id

router = APIRouter(prefix="/ledger", tags=["Ledger"])


@router.get("/{wallet_id}")
async def get_ledger(
    wallet_id: str,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated ledger entries for a wallet."""
    wallet = await get_wallet_by_id(db, wallet_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    if str(wallet.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your wallet"
        )
    entries = await get_wallet_ledger(db, wallet_id, limit, offset)
    return [
        {
            "id": str(e.id),
            "transaction_id": str(e.transaction_id),
            "wallet_id": str(e.wallet_id),
            "entry_type": e.entry_type,
            "amount": str(e.amount),
            "balance_before": str(e.balance_before),
            "balance_after": str(e.balance_after),
            "created_at": str(e.created_at)
        }
        for e in entries
    ]