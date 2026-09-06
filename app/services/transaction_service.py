import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.ledger_entry import LedgerEntry
from app.cache.redis_client import invalidate_wallet_cache


class InsufficientFundsError(Exception):
    pass


class WalletNotFoundError(Exception):
    pass


async def transfer(
    sender_wallet_id: str,
    receiver_wallet_id: str,
    amount: Decimal,
    db: AsyncSession,
) -> Transaction:
    if amount <= Decimal("0"):
        raise ValueError("Transfer amount must be positive")

    if sender_wallet_id == receiver_wallet_id:
        raise ValueError("Cannot transfer to same wallet")

    sender_result = await db.execute(
        select(Wallet)
        .where(Wallet.id == uuid.UUID(sender_wallet_id))
        .with_for_update()
    )
    sender = sender_result.scalar_one_or_none()

    if not sender:
        raise WalletNotFoundError(f"Sender wallet {sender_wallet_id} not found")

    receiver_result = await db.execute(
        select(Wallet)
        .where(Wallet.id == uuid.UUID(receiver_wallet_id))
        .with_for_update()
    )
    receiver = receiver_result.scalar_one_or_none()

    if not receiver:
        raise WalletNotFoundError(f"Receiver wallet {receiver_wallet_id} not found")

    if sender.balance < amount:
        raise InsufficientFundsError(
            f"Insufficient funds. Balance: {sender.balance}, Required: {amount}"
        )

    sender_balance_before = sender.balance
    receiver_balance_before = receiver.balance

    sender.balance -= amount
    receiver.balance += amount

    transaction = Transaction(
        sender_wallet_id=uuid.UUID(sender_wallet_id),
        receiver_wallet_id=uuid.UUID(receiver_wallet_id),
        amount=amount,
        status="completed"
    )
    db.add(transaction)
    await db.flush()

    debit_entry = LedgerEntry(
        transaction_id=transaction.id,
        wallet_id=uuid.UUID(sender_wallet_id),
        entry_type="debit",
        amount=amount,
        balance_before=sender_balance_before,
        balance_after=sender.balance
    )
    credit_entry = LedgerEntry(
        transaction_id=transaction.id,
        wallet_id=uuid.UUID(receiver_wallet_id),
        entry_type="credit",
        amount=amount,
        balance_before=receiver_balance_before,
        balance_after=receiver.balance
    )
    db.add(debit_entry)
    db.add(credit_entry)

    await db.commit()

    # Invalidate Redis cache for both wallets after transfer
    await invalidate_wallet_cache(sender_wallet_id)
    await invalidate_wallet_cache(receiver_wallet_id)

    return transaction