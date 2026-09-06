import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from app.models.wallet import Wallet
from app.models.user import User


async def create_wallet(
    db: AsyncSession,
    user: User,
    currency: str = "INR"
) -> Wallet:
    """Create a new wallet for a user."""
    wallet = Wallet(
        user_id=user.id,
        balance=Decimal("0.00"),
        currency=currency
    )
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet


async def get_wallet_by_id(
    db: AsyncSession,
    wallet_id: str
) -> Wallet | None:
    """Get a wallet by ID."""
    result = await db.execute(
        select(Wallet).where(Wallet.id == uuid.UUID(wallet_id))
    )
    return result.scalar_one_or_none()


async def get_user_wallets(
    db: AsyncSession,
    user: User
) -> list[Wallet]:
    """Get all wallets for a user."""
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == user.id)
    )
    return result.scalars().all()


async def get_wallet_balance(
    db: AsyncSession,
    wallet_id: str
) -> Decimal:
    """Get current balance of a wallet."""
    wallet = await get_wallet_by_id(db, wallet_id)
    if not wallet:
        raise ValueError(f"Wallet {wallet_id} not found")
    return wallet.balance