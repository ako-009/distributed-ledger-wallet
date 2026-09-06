import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.ledger_entry import LedgerEntry


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
    """
    Atomic transfer between two wallets.

    This function:
    1. Locks both wallets with SELECT FOR UPDATE (prevents double-spend)
    2. Validates sender has sufficient balance
    3. Debits sender, credits receiver
    4. Creates transaction record
    5. Creates immutable ledger entries
    6. Commits everything atomically (ACID)
    """

    if amount <= Decimal("0"):
        raise ValueError("Transfer amount must be positive")

    if sender_wallet_id == receiver_wallet_id:
        raise ValueError("Cannot transfer to same wallet")

    # Step 1: Lock both wallets with SELECT FOR UPDATE
    # This prevents any other transaction from modifying these wallets
    # until we commit. This is PESSIMISTIC LOCKING.
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

    # Step 2: Validate balance
    if sender.balance < amount:
        raise InsufficientFundsError(
            f"Insufficient funds. Balance: {sender.balance}, Required: {amount}"
        )

    # Step 3: Record balances before the transfer
    sender_balance_before = sender.balance
    receiver_balance_before = receiver.balance

    # Step 4: Debit sender, credit receiver
    sender.balance -= amount
    receiver.balance += amount

    # Step 5: Create transaction record
    transaction = Transaction(
        sender_wallet_id=uuid.UUID(sender_wallet_id),
        receiver_wallet_id=uuid.UUID(receiver_wallet_id),
        amount=amount,
        status="completed"
    )
    db.add(transaction)

    # Flush to get the transaction ID before creating ledger entries
    await db.flush()

    # Step 6: Create immutable ledger entries
    # Debit entry for sender
    debit_entry = LedgerEntry(
        transaction_id=transaction.id,
        wallet_id=uuid.UUID(sender_wallet_id),
        entry_type="debit",
        amount=amount,
        balance_before=sender_balance_before,
        balance_after=sender.balance
    )

    # Credit entry for receiver
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

    # Step 7: Commit everything atomically
    # If ANY step above failed, SQLAlchemy rolls back ALL changes
    await db.commit()

    return transaction