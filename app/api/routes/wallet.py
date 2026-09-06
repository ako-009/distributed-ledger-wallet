import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.wallet import WalletCreate, WalletResponse, BalanceResponse
from app.services.wallet_service import (
    create_wallet, get_wallet_by_id, get_user_wallets
)
from app.cache.redis_client import (
    get_cached_balance, set_cached_balance, invalidate_wallet_cache
)

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.post("/create", response_model=WalletResponse, status_code=201)
async def create_new_wallet(
    wallet_data: WalletCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new wallet for the authenticated user."""
    wallet = await create_wallet(db, current_user, wallet_data.currency)
    return WalletResponse(
        id=str(wallet.id),
        user_id=str(wallet.user_id),
        balance=wallet.balance,
        currency=wallet.currency,
        is_active=wallet.is_active
    )


@router.get("/my-wallets", response_model=list[WalletResponse])
async def get_my_wallets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all wallets for the authenticated user."""
    wallets = await get_user_wallets(db, current_user)
    return [
        WalletResponse(
            id=str(w.id),
            user_id=str(w.user_id),
            balance=w.balance,
            currency=w.currency,
            is_active=w.is_active
        )
        for w in wallets
    ]


@router.get("/{wallet_id}/balance", response_model=BalanceResponse)
async def get_balance(
    wallet_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get wallet balance.
    Cache-aside pattern:
    1. Check Redis first
    2. Cache HIT → return immediately (no DB query)
    3. Cache MISS → query DB → store in Redis → return
    """
    # Step 1: Check Redis cache
    cached_balance = await get_cached_balance(wallet_id)

    if cached_balance is not None:
        # CACHE HIT — return without touching PostgreSQL
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
        return BalanceResponse(
            wallet_id=wallet_id,
            balance=cached_balance,
            currency="INR",
            cache_hit=True
        )

    # Step 2: CACHE MISS — query PostgreSQL
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

    # Step 3: Store in Redis for next time
    await set_cached_balance(wallet_id, wallet.balance, wallet.currency)

    return BalanceResponse(
        wallet_id=str(wallet.id),
        balance=wallet.balance,
        currency=wallet.currency,
        cache_hit=False
    )


@router.post("/{wallet_id}/deposit", response_model=WalletResponse)
async def deposit(
    wallet_id: str,
    amount: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Deposit money into a wallet (for testing purposes)."""
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
    wallet.balance += Decimal(str(amount))
    await db.commit()
    await db.refresh(wallet)

    # Invalidate cache after deposit
    await invalidate_wallet_cache(wallet_id)

    return WalletResponse(
        id=str(wallet.id),
        user_id=str(wallet.user_id),
        balance=wallet.balance,
        currency=wallet.currency,
        is_active=wallet.is_active
    )